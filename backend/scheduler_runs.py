"""Bounded, persisted evidence of scheduled execution, independent of news output.

Only scheduler registration wrappers use this module. Manual task calls do not
prove cron operation. Fixed job documents do not accumulate run history or text.
"""
import asyncio
from datetime import datetime, timedelta, timezone
import logging
import os
from uuid import uuid4

logger = logging.getLogger(__name__)
RECORD_TIMEOUT_SECONDS = 3
JOB_CONFIG = {
    "rss": {"interval_seconds": 120, "max_runtime_seconds": 180},
    "speed": {"interval_seconds": 60, "max_runtime_seconds": 3660},
    "gpt": {"interval_seconds": 300, "max_runtime_seconds": 780},
}
JOB_STATUSES = frozenset({"starting", "running", "ok", "degraded", "failed", "blocked", "paused", "overdue", "stalled", "unknown", "disabled"})
JOB_OUTCOMES = frozenset({"ok", "degraded", "failed", "blocked", "paused", "cancelled"})
SCHEDULER_STATES = frozenset({"running", "paused", "stopped", "not_started", "disabled"})
JOB_ERROR_CODES = frozenset({"job_exception", "job_timeout", "job_cancelled", "invalid_result", "task_reported_error", "no_active_feeds", "all_feeds_failed", "partial_feed_failure", "processing_errors", "rewrite_errors", "provider_blocked", "start_record_failed", "finish_record_failed"})
SCHEDULER_WARNING_CODES = frozenset(
    {"scheduler_paused", "scheduler_not_running", "scheduler_telemetry_unavailable"}
    | {f"scheduler_{job}_{state}" for job in JOB_CONFIG
       for state in ("stalled", "overdue", "failed", "degraded", "blocked", "unknown")})
COUNT_FIELDS = {
    "rss": ("new_events", "duplicates", "feeds_checked", "feed_errors"),
    "speed": ("processed", "created_draft", "updated", "review", "skipped", "retry", "errors"),
    "gpt": ("rewritten", "published", "rejected", "errors"),
}
JOB_RUN_FIELDS = {"_id": 1, "boot_id": 1, "state": 1, "last_started_at": 1,
                  "last_finished_at": 1, "last_success_at": 1, "last_error_at": 1,
                  "last_error_code": 1, "last_outcome": 1, "counts": 1}


def utcnow():
    return datetime.now(timezone.utc)


_boot_id = uuid4().hex
_started_at = utcnow()
_state_reader = None
_recording_errors = {}


def begin_scheduler_epoch(state_reader):
    """Called synchronously at scheduler start, before its first scheduled run."""
    global _boot_id, _started_at, _state_reader
    _boot_id, _started_at, _state_reader = uuid4().hex, utcnow(), state_reader
    _recording_errors.clear()


def runtime_context():
    enabled = os.environ.get("SCHEDULER_ENABLED", "true").lower() in {"true", "1", "yes"}
    try:
        state = _state_reader() if _state_reader is not None else "not_started"
    except Exception:
        state = "not_started"
    return {"boot_id": _boot_id, "started_at": _started_at, "enabled": enabled,
            "scheduler_state": state if state in SCHEDULER_STATES else "not_started",
            "recording_errors": dict(_recording_errors)}


def _count(value):
    if type(value) is int:
        return max(0, value)
    return len(value) if isinstance(value, (list, dict, tuple)) else 0


def classify_job_result(job, result):
    """Return only enum outcome/error and numeric allowlisted counters."""
    if not isinstance(result, dict):
        return "failed", "invalid_result", {}
    counts = {key: _count(result.get(key)) for key in COUNT_FIELDS[job]}
    if result.get("error"):
        return "failed", "task_reported_error", counts
    if job == "rss":
        if counts["feeds_checked"] == 0:
            return "failed", "no_active_feeds", counts
        if counts["feed_errors"] >= counts["feeds_checked"]:
            return "failed", "all_feeds_failed", counts
        if counts["feed_errors"]:
            return "degraded", "partial_feed_failure", counts
    elif job == "speed" and (counts["errors"] or counts["retry"]):
        return "degraded", "processing_errors", counts
    elif job == "gpt":
        if result.get("blocked"):
            return "blocked", "provider_blocked", counts
        if result.get("paused"):
            return "paused", None, counts
        if counts["errors"]:
            return "degraded", "rewrite_errors", counts
    return "ok", None, counts


async def run_scheduled_job(db, job, operation):
    """Observe a regular invocation without changing its workload or retry rules.

    Metadata I/O has a separate deadline and cannot stop editorial work. A local
    recording fault makes diagnostics unknown, never an apparent worker hang.
    """
    if job not in JOB_CONFIG:
        raise ValueError("unknown_scheduled_job")
    context = runtime_context()
    token, started = uuid4().hex, utcnow()
    selector = {"_id": job, "boot_id": context["boot_id"], "run_id": token}
    recorded = False
    try:
        await asyncio.wait_for(db.pipeline_job_runs.update_one({"_id": job}, {
            "$set": {"boot_id": context["boot_id"], "run_id": token,
                     "state": "running", "last_started_at": started,
                     "runtime_started_at": context["started_at"]},
            "$inc": {"started_count": 1},
        }, upsert=True), timeout=RECORD_TIMEOUT_SECONDS)
        recorded = True
        _recording_errors.pop(job, None)
    except asyncio.CancelledError:
        _recording_errors[job] = "start_record_failed"
        raise
    except Exception:
        _recording_errors[job] = "start_record_failed"
        logger.warning("[JOB:%s] start_record_failed", job)

    outcome, error, counts = "failed", "job_exception", {}
    try:
        result = await operation()
        outcome, error, counts = classify_job_result(job, result)
        return result
    except asyncio.CancelledError:
        outcome, error = "cancelled", "job_cancelled"
        raise
    except Exception as exc:
        error = "job_timeout" if isinstance(exc, TimeoutError) else "job_exception"
        logger.warning("[JOB:%s] %s", job, error)
        return {"error": error}
    finally:
        if recorded:
            finished = utcnow()
            fields = {"state": "finished", "last_finished_at": finished,
                      "last_outcome": outcome, "counts": counts}
            if outcome == "ok":
                fields["last_success_at"] = finished
            if error:
                fields.update(last_error_at=finished, last_error_code=error)
            try:
                # A slow previous worker can never finish a newer worker's run.
                await asyncio.wait_for(db.pipeline_job_runs.update_one(selector, {
                    "$set": fields, "$unset": {"run_id": ""},
                }), timeout=RECORD_TIMEOUT_SECONDS)
            except asyncio.CancelledError:
                _recording_errors[job] = "finish_record_failed"
                raise
            except Exception:
                _recording_errors[job] = "finish_record_failed"
                logger.warning("[JOB:%s] finish_record_failed", job)


def _time(value, now):
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
        parsed = parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)
        return parsed if parsed <= now else None
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def summarize_scheduler_runs(records, now=None, runtime=None):
    """Public allowlist; stalled requires an actual current-boot running record."""
    now, runtime = now or utcnow(), runtime or runtime_context()
    started = _time(runtime.get("started_at"), now) or now
    enabled = runtime.get("enabled") is True
    scheduler_state = runtime.get("scheduler_state")
    scheduler_state = scheduler_state if scheduler_state in SCHEDULER_STATES else "not_started"
    if not enabled:
        scheduler_state = "disabled"
    rows = {row["_id"]: row for row in records if isinstance(row.get("_id"), str) and row["_id"] in JOB_CONFIG}
    jobs, warnings = {}, []
    if enabled and scheduler_state == "paused":
        warnings.append("scheduler_paused")
    for job, config in JOB_CONFIG.items():
        row = rows.get(job, {})
        times = {key: _time(row.get(key), now) for key in (
            "last_started_at", "last_finished_at", "last_success_at", "last_error_at")}
        grace = started + timedelta(seconds=config["interval_seconds"] + 60)
        current = row.get("boot_id") == runtime.get("boot_id") and bool(row)
        recording_error = runtime.get("recording_errors", {}).get(job)
        recording_error = recording_error if recording_error in {"start_record_failed", "finish_record_failed"} else None
        outcome = row.get("last_outcome") if isinstance(row.get("last_outcome"), str) and row["last_outcome"] in JOB_OUTCOMES else None
        if not enabled:
            status = "disabled"
        elif scheduler_state == "paused":
            status = "paused"
        elif recording_error:
            status = "unknown"
        elif not current or not times["last_started_at"]:
            status = "starting" if now <= grace else "overdue"
        elif scheduler_state != "running":
            status = "starting" if now <= grace else "overdue"
        elif row.get("state") == "running":
            elapsed = (now - times["last_started_at"]).total_seconds()
            status = "stalled" if elapsed > config["max_runtime_seconds"] else "running"
        elif row.get("state") != "finished" or not times["last_finished_at"] or not outcome:
            status = "unknown"
        elif (now - times["last_finished_at"]).total_seconds() > 2 * config["interval_seconds"] + 60:
            status = "overdue"
        else:
            status = "failed" if outcome == "cancelled" else outcome
        code = f"scheduler_{job}_{status}"
        if code in SCHEDULER_WARNING_CODES:
            warnings.append(code)
        jobs[job] = {"status": status, "current_boot": current,
                     **{key: value.isoformat() if value else None for key, value in times.items()},
                     "last_error_code": row.get("last_error_code") if isinstance(row.get("last_error_code"), str) and row["last_error_code"] in JOB_ERROR_CODES else None,
                     "last_outcome": outcome, **config, "grace_until": grace.isoformat(),
                     "counts": {key: _count((row.get("counts") if isinstance(row.get("counts"), dict) else {}).get(key)) for key in COUNT_FIELDS[job]},
                     "recording_error": recording_error}
    if enabled and scheduler_state not in {"running", "paused"} and all(now > started + timedelta(seconds=c["interval_seconds"] + 60) for c in JOB_CONFIG.values()):
        warnings.append("scheduler_not_running")
    status = "disabled" if not enabled else "warning" if warnings else "starting" if any(j["status"] == "starting" for j in jobs.values()) else "ok"
    return {"status": status, "scheduler_state": scheduler_state, "started_at": started.isoformat(),
            "warnings": warnings, "jobs": jobs}


async def collect_scheduler_run_health(db, now=None):
    records = [record async for record in db.pipeline_job_runs.find(
        {"_id": {"$in": list(JOB_CONFIG)}}, JOB_RUN_FIELDS)]
    return summarize_scheduler_runs(records, now=now)
