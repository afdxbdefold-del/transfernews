#!/usr/bin/env python3
"""External, credential-free production checks. No publishing or server writes."""
import json
import time
import urllib.request
from datetime import datetime, timezone

ORIGIN = "https://transfernews.de"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def recent(value, now, seconds):
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return date.tzinfo is not None and 0 <= (now - date).total_seconds() <= seconds
    except (TypeError, ValueError, AttributeError):
        return False


def assess(ready, health, now=None):
    now = now or datetime.now(timezone.utc)
    errors = []
    if not isinstance(ready, dict) or not isinstance(health, dict):
        return ["invalid_diagnostic_response"]
    scheduler = ready.get("scheduler")
    if (ready.get("status") != "ready" or ready.get("database") is not True
            or not isinstance(scheduler, dict) or scheduler.get("enabled") is not True
            or scheduler.get("running") is not True):
        errors.append("application_not_ready")
    if not recent(health.get("checked_at"), now, 300):
        errors.append("diagnostics_not_current")
    if health.get("status") not in {"ok", "idle"} or health.get("warnings") != []:
        errors.append("pipeline_requires_attention")
    jobs = health.get("scheduler_jobs")
    if not isinstance(jobs, dict) or jobs.get("status") not in {"ok", "running", "starting"}:
        errors.append("scheduler_runs_not_verified")
    watchdog = health.get("watchdog")
    if not isinstance(watchdog, dict) or not recent(watchdog.get("checked_at"), now, 1200):
        errors.append("host_watchdog_not_current")
    elif (watchdog.get("status") not in {"healthy", "recovering"}
          and not (watchdog.get("status") == "paused" and watchdog.get("reason") == "startup_grace"
                   and isinstance(jobs, dict) and recent(jobs.get("started_at"), now, 900))):
        errors.append("host_watchdog_requires_attention")
    return errors


def fetch(path, *, as_json=True):
    request = urllib.request.Request(ORIGIN + path, headers={"User-Agent": "Transfernews-Operations-Monitor/1.0"})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=15) as response:
        if response.status != 200:
            raise ValueError("unexpected_http_status")
        body = response.read(2_000_001)
    if len(body) > 2_000_000:
        raise ValueError("unexpected_response_size")
    return json.loads(body) if as_json else body


def check_once():
    try:
        home = fetch("/", as_json=False)
        errors = [] if b"transfernews" in home.lower() else ["homepage_content_missing"]
        return errors + assess(fetch("/api/ready"), fetch("/api/pipeline/health"))
    except Exception:
        # Never copy arbitrary server text, URLs, exception bodies or credentials.
        return ["public_request_failed"]


def main():
    errors = check_once()
    if errors:
        time.sleep(20)
        errors = check_once()
    print(json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(),
                      "status": "failed" if errors else "ok", "errors": errors}))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
