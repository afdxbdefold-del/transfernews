"""Read-only editorial throughput diagnostics, deliberately separate from readiness.

Times describe persisted work, not a scheduler invocation that found no new work.
A publication warning requests investigation; it never bypasses editorial gates.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from rewrite_errors import AUTH_CODES, BILLING_CODES, TRANSIENT_CODES
from scheduler_runs import collect_scheduler_run_health, SCHEDULER_WARNING_CODES


EVENT_STATES = ("pending", "retry", "processing", "review", "processed", "error", "rejected", "published")
ARTICLE_STATES = ("draft", "published", "archived")
REWRITE_STATES = ("pending", "retry", "processing", "review", "failed", "blocked", "complete")
EVENT_FIELDS = {"_id": 0, "status": 1, "created_at": 1, "processed_at": 1, "source_published_at": 1}
ARTICLE_FIELDS = {"_id": 0, "status": 1, "published_at": 1, "gpt_rewritten_at": 1, "rewrite_status": 1, "needs_gpt_rewrite": 1}
PROVIDER_FIELDS = {"_id": 0, "status": 1, "error_code": 1, "error_kind": 1, "retry_at": 1}
PROVIDER_ERROR_KINDS = {"billing", "authentication", "configuration", "rate_limit", "upstream", "timeout", "connection"}
# Historical/unrecognized values are redacted rather than copied publicly.
PROVIDER_ERROR_CODES = AUTH_CODES | BILLING_CODES | TRANSIENT_CODES | {
    "provider_access_denied", "invalid_retry_after", "unclassified_rate_limit",
    "provider_unavailable", "provider_timeout", "provider_connection_error",
    "provider_request_rejected", "missing_openai_key",
}
WATCHDOG_FIELDS = {"_id": 0, "checked_at": 1, "status": 1, "action": 1, "reason": 1,
                   "consecutive_failures": 1, "restart_attempts_6h": 1, "last_restart_at": 1}
WATCHDOG_STATUSES = {"healthy", "warning", "recovering", "paused", "error"}
WATCHDOG_ACTIONS = {"none", "would_restart", "restart_attempted", "restarted", "restart_failed"}
WATCHDOG_REASONS = {
    "ready", "ready_unavailable", "ready_unhealthy", "scheduler_stopped", "scheduler_job_stalled",
    "startup_grace", "maintenance", "deployment_active", "target_ambiguous", "target_changed",
    "mongo_unhealthy", "invalid_state", "lock_busy", "threshold_pending", "cooldown",
    "restart_budget_exhausted", "probe_failed", "restart_failed", "state_write_failed",
    "diagnostic_publish_failed",
}
THROUGHPUT_WINDOW_HOURS = 6
THROUGHPUT_MIN_FRESH_IMPORTS = 10


def _time(value, now, allow_future=False):
    try:
        result = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else None
        if result is None:
            return None
        if result.tzinfo is None:  # Motor returns naive UTC for BSON dates by default.
            result = result.replace(tzinfo=timezone.utc)
        result = result.astimezone(timezone.utc)
        return result if allow_future or result <= now else None
    except (ValueError, TypeError, OverflowError):
        return None


class PipelineHealthSnapshot:
    """Accumulate projected records without retaining article text or event content."""
    def __init__(self, now=None):
        self.now = now or datetime.now(timezone.utc)
        if self.now.tzinfo is None:
            self.now = self.now.replace(tzinfo=timezone.utc)
        self.now = self.now.astimezone(timezone.utc)
        self.cutoff = self.now - timedelta(hours=24)
        self.throughput_cutoff = self.now - timedelta(hours=THROUGHPUT_WINDOW_HOURS)
        self.events = Counter()
        self.articles = Counter()
        self.rewrites = Counter()
        self.quality = Counter()
        self.activity = Counter()
        self.last = dict(imported_at=None, processed_at=None, rewritten_at=None, published_at=None)
        self.first_import = None
        self.provider = {"status": "not_recorded", "error_code": None, "error_kind": None, "retry_at": None}
        self.scheduler_jobs = {"status": "unknown", "scheduler_state": "not_started",
                               "started_at": None, "warnings": [], "jobs": {}}
        self.watchdog = {"checked_at": None, "status": "unknown", "action": None, "reason": None,
                         "consecutive_failures": None, "restart_attempts_6h": None, "last_restart_at": None}
        self.watchdog_warnings = []

    def add_scheduler_jobs(self, snapshot):
        """The dedicated helper supplies sanitized, fixed-schema job records."""
        if not snapshot:
            return
        self.scheduler_jobs = {key: snapshot.get(key) for key in (
            "status", "scheduler_state", "started_at", "jobs")}
        self.scheduler_jobs["warnings"] = sorted({
            code for code in snapshot.get("warnings", [])
            if isinstance(code, str) and code in SCHEDULER_WARNING_CODES})

    def add_watchdog(self, record):
        if record is None:
            return  # Not installed yet is unknown, not a false alarm.
        checked = _time(record.get("checked_at"), self.now)
        restarted = _time(record.get("last_restart_at"), self.now)
        status, action, reason = (record.get(key) for key in ("status", "action", "reason"))
        counters = {key: value if type(value) is int and 0 <= value <= 2**31 - 1 else None
                    for key in ("consecutive_failures", "restart_attempts_6h")
                    for value in (record.get(key),)}
        valid_status = isinstance(status, str) and status in WATCHDOG_STATUSES
        valid_action = isinstance(action, str) and action in WATCHDOG_ACTIONS
        valid_reason = isinstance(reason, str) and reason in WATCHDOG_REASONS
        valid = (checked is not None and valid_status and valid_action and valid_reason
                 and all(value is not None for value in counters.values())
                 and (record.get("last_restart_at") is None or restarted is not None))
        self.watchdog = {"checked_at": checked.isoformat() if checked else None,
                         "status": status if valid else "unknown",
                         "action": action if valid_action else "unknown",
                         "reason": reason if valid_reason else "unknown", **counters,
                         "last_restart_at": restarted.isoformat() if restarted else None}
        self.watchdog_warnings = []
        if not valid:
            self.watchdog_warnings.append("watchdog_state_unknown")
        if checked and self.now - checked > timedelta(minutes=20):
            self.watchdog_warnings.append("watchdog_stale")
        if valid_status and status in {"warning", "error"}:
            self.watchdog_warnings.append("watchdog_warning")

    def add_provider(self, provider):
        if not provider:
            return
        status, code, kind = (provider.get(key) for key in ("status", "error_code", "error_kind"))
        retry = _time(provider.get("retry_at"), self.now, allow_future=True)
        self.provider = {
            "status": status if status in ("ready", "retry", "blocked") else "unknown",
            "error_code": code if isinstance(code, str) and code in PROVIDER_ERROR_CODES else "unknown" if code else None,
            "error_kind": kind if isinstance(kind, str) and kind in PROVIDER_ERROR_KINDS else "unknown" if kind else None,
            "retry_at": retry.isoformat() if retry else None,
        }

    def _record_time(self, key, value):
        timestamp = _time(value, self.now)
        if timestamp is not None and (self.last[key] is None or timestamp > self.last[key]):
            self.last[key] = timestamp
        return timestamp

    def add_event(self, event):
        state = event.get("status")
        self.events[state if state in EVENT_STATES else "unknown"] += 1
        imported = self._record_time("imported_at", event.get("created_at"))
        if imported is None:
            self.quality["events_without_valid_import_time"] += 1
        else:
            self.first_import = min(self.first_import or imported, imported)
            source_time = _time(event.get("source_published_at"), self.now)
            if imported >= self.throughput_cutoff:
                self.activity["imports_last_6h"] += 1
                # A reimport of yesterday's source is not new source supply.
                # Keep the existing 24h/48h freshness diagnostic separate.
                if source_time and source_time >= self.throughput_cutoff:
                    self.activity["fresh_imports_last_6h"] += 1
            if imported >= self.cutoff:
                self.activity["imports_last_24h"] += 1
                if source_time and source_time >= self.now - timedelta(hours=48):
                    self.activity["fresh_imports_last_24h"] += 1
        processed = self._record_time("processed_at", event.get("processed_at"))
        if processed and processed >= self.cutoff:
            self.activity["processed_last_24h"] += 1
        if processed and processed >= self.throughput_cutoff:
            self.activity["processed_last_6h"] += 1

    def add_article(self, article):
        state = article.get("status")
        self.articles[state if state in ARTICLE_STATES else "unknown"] += 1
        rewrite = article.get("rewrite_status")
        # Legacy queued records can lack rewrite_status; the worker accepts them.
        if not rewrite and article.get("needs_gpt_rewrite") is True:
            rewrite = "pending"
        self.rewrites[rewrite if rewrite in REWRITE_STATES else "unknown"] += 1
        if article.get("needs_gpt_rewrite") is True and rewrite not in ("review", "failed", "blocked", "processing"):
            self.activity["rewrite_waiting"] += 1
        rewritten = self._record_time("rewritten_at", article.get("gpt_rewritten_at"))
        if rewritten and rewritten >= self.cutoff:
            self.activity["rewritten_last_24h"] += 1
        if rewritten and rewritten >= self.throughput_cutoff:
            self.activity["rewritten_last_6h"] += 1
        if state != "published":
            return  # A draft's inherited published_at must not hide a stalled pipeline.
        published = self._record_time("published_at", article.get("published_at"))
        if published is None:
            self.quality["published_articles_without_valid_date"] += 1
        else:
            if published >= self.cutoff:
                self.activity["published_last_24h"] += 1
            # Exactly six hours without publication reaches the warning boundary.
            if published > self.throughput_cutoff:
                self.activity["published_last_6h"] += 1
            if published >= self.now - timedelta(hours=1):
                self.activity["published_last_hour"] += 1

    def result(self):
        warnings = list(self.scheduler_jobs["warnings"]) + self.watchdog_warnings
        if self.provider["status"] == "blocked":
            warnings.append("rewrite_provider_blocked")
        fresh = self.activity["fresh_imports_last_24h"]
        last_publication = self.last["published_at"]
        publication_gap = (self.now - last_publication).total_seconds() / 3600 if last_publication else None
        if fresh:
            if self.quality["published_articles_without_valid_date"]:
                warnings.append("publication_timestamp_unknown")
            elif publication_gap is not None and publication_gap >= 24:
                warnings.append("publication_stalled")
            elif not self.articles["published"] and self.first_import and self.first_import <= self.cutoff:
                warnings.append("publication_stalled")
        no_recent_publication = (
            publication_gap is not None and publication_gap >= THROUGHPUT_WINDOW_HOURS
        ) or (
            not self.articles["published"] and self.first_import is not None
            and self.first_import <= self.throughput_cutoff
        )
        if (self.activity["fresh_imports_last_6h"] >= THROUGHPUT_MIN_FRESH_IMPORTS
                and no_recent_publication and not self.quality["published_articles_without_valid_date"]):
            warnings.append("publication_throughput_low")
        waiting = self.events["pending"] + self.events["retry"]
        if waiting > 50:
            warnings.append("event_backlog")
        if warnings:
            status = "warning"
        elif not sum(self.events.values()) and not sum(self.articles.values()):
            status = "initializing"
        elif sum(self.events.values()) and self.last["imported_at"] is None:
            status = "unknown"
        elif not fresh:
            status = "idle"
        elif last_publication is None:
            status = "initializing"
        else:
            status = "ok"
        return {
            "status": status, "checked_at": self.now.isoformat(), "readiness_impact": False,
            "warnings": warnings,
            "provider": self.provider,
            "scheduler_jobs": self.scheduler_jobs,
            "watchdog": self.watchdog,
            "last_activity": {key: value.isoformat() if value else None for key, value in self.last.items()},
            "publication_gap_hours": round(publication_gap, 2) if publication_gap is not None else None,
            "activity": {key: self.activity[key] for key in (
                "imports_last_6h", "fresh_imports_last_6h", "processed_last_6h",
                "rewritten_last_6h", "published_last_6h",
                "imports_last_24h", "fresh_imports_last_24h", "processed_last_24h",
                "rewritten_last_24h", "published_last_24h", "published_last_hour")},
            "stages": {
                "events": {key: self.events[key] for key in (*EVENT_STATES, "unknown")},
                "articles": {key: self.articles[key] for key in (*ARTICLE_STATES, "unknown")},
                "rewrite": {**{key: self.rewrites[key] for key in (*REWRITE_STATES, "unknown")}, "waiting": self.activity["rewrite_waiting"]},
                "event_waiting": waiting,
            },
            "data_quality": {key: self.quality[key] for key in (
                "events_without_valid_import_time", "published_articles_without_valid_date")},
            "thresholds": {"publication_gap_hours": 24, "import_lookback_hours": 24,
                           "source_freshness_hours": 48, "watchdog_stale_minutes": 20,
                           "publication_throughput_gap_hours": THROUGHPUT_WINDOW_HOURS,
                           "throughput_import_lookback_hours": THROUGHPUT_WINDOW_HOURS,
                           "throughput_source_freshness_hours": THROUGHPUT_WINDOW_HOURS,
                           "throughput_min_fresh_imports": THROUGHPUT_MIN_FRESH_IMPORTS},
        }


async def collect_pipeline_health(db, now=None):
    """Stream only diagnostic fields; no writes, scheduler startup, or external calls."""
    snapshot = PipelineHealthSnapshot(now)
    async for event in db.events.find({}, EVENT_FIELDS):
        snapshot.add_event(event)
    async for article in db.articles.find({}, ARTICLE_FIELDS):
        snapshot.add_article(article)
    snapshot.add_provider(await db.rewrite_provider_state.find_one({"_id": "openai_rewrite"}, PROVIDER_FIELDS))
    snapshot.add_scheduler_jobs(await collect_scheduler_run_health(db, now=snapshot.now))
    snapshot.add_watchdog(await db.ops_watchdog.find_one({"_id": "host_watchdog"}, WATCHDOG_FIELDS))
    return snapshot.result()


class HealthWarningThrottle:
    """One warning per episode/code, repeated at most every six hours per process."""
    def __init__(self, interval=timedelta(hours=6)):
        self.interval = interval
        self.last_logged = {}

    def update(self, warnings, now=None, *, complete=True):
        now = now or datetime.now(timezone.utc)
        active = set(warnings)
        recovered = sorted(set(self.last_logged) - active) if complete else []
        for code in recovered:
            del self.last_logged[code]
        emitted = []
        for code in sorted(active):
            previous = self.last_logged.get(code)
            if previous is None or now - previous >= self.interval:
                self.last_logged[code] = now
                emitted.append(code)
        return emitted, recovered
