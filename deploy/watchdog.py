#!/usr/bin/env python3
"""Bounded host recovery for the existing Transfernews backend; read-only by default."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
from datetime import datetime, timedelta, timezone

APP = "t4iysn7locgn8jdax7xb6s9j"
ROOT = Path("/opt/transfernews-ops/watchdog")
STATUS = {"healthy", "warning", "recovering", "paused", "error"}
ACTIONS = {"none", "would_restart", "restart_attempted", "restarted", "restart_failed"}
REASONS = {"ready", "ready_unavailable", "ready_unhealthy", "scheduler_stopped", "scheduler_job_stalled",
           "startup_grace", "maintenance", "deployment_active", "target_ambiguous", "target_changed",
           "mongo_unhealthy", "invalid_state", "lock_busy", "threshold_pending", "cooldown",
           "restart_budget_exhausted", "probe_failed", "restart_failed", "state_write_failed", "diagnostic_publish_failed"}
RECOVERABLE = {"ready_unavailable", "ready_unhealthy", "scheduler_stopped", "scheduler_job_stalled"}
INSPECT = ('{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Config.Image}},'
           '"labels":{{json .Config.Labels}},"running":{{json .State.Running}},'
           '"started_at":{{json .State.StartedAt}},"health":'
           '{{with (index .State "Health")}}{{json (index . "Status")}}{{else}}null{{end}}}')


def utcnow():
    return datetime.now(timezone.utc)


def stamp(value):
    return value.astimezone(timezone.utc).isoformat()


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return parsed.astimezone(timezone.utc)


class Runner:
    def __init__(self):
        self.deadline = time.monotonic() + 90

    def __call__(self, args, timeout=10):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("watchdog deadline")
        return subprocess.run(args, check=True, capture_output=True, text=True,
                              timeout=min(timeout, remaining)).stdout


def inventory(run):
    ids = run(["docker", "ps", "-aq"], 8).split()
    if not ids:
        return []
    return [json.loads(line) for line in run(["docker", "inspect", "--format", INSPECT, *ids], 10).splitlines()]


def select(containers, service):
    matches = []
    for item in containers:
        labels = item.get("labels") or {}
        if (item.get("running") is True and item.get("name", "").lstrip("/").startswith(service + "-" + APP + "-")
                and labels.get("com.docker.compose.project") == APP
                and labels.get("com.docker.compose.service") == service
                and labels.get("coolify.managed") == "true"):
            matches.append(item)
    return matches[0] if len(matches) == 1 else None


def local_http(run, container_id, path, timeout):
    # No server imports, credentials, external network, or scheduler startup.
    script = ("import json,urllib.request,urllib.error\n"
              "try:\n r=urllib.request.urlopen(" + repr("http://127.0.0.1:8001/api/" + path)
              + ",timeout=" + str(timeout) + ")\nexcept urllib.error.HTTPError as e:\n r=e\n"
              "print(json.dumps({'code':r.status,'body':json.loads(r.read(262144))}))")
    try:
        value = json.loads(run(["docker", "exec", container_id, "python", "-c", script], timeout + 3))
        return value if isinstance(value, dict) and isinstance(value.get("body"), dict) else None
    except Exception:
        return None


def observe(run, now, maintenance=False, clock=None):
    clock = clock or utcnow
    if maintenance:
        return {"reason": "maintenance"}
    try:
        containers = inventory(run)
        if any(c.get("running") is True and "coollabsio/coolify-helper" in c.get("image", "") for c in containers):
            return {"reason": "deployment_active"}
        backend, mongo = select(containers, "backend"), select(containers, "mongodb")
        if not backend or not mongo:
            return {"reason": "target_ambiguous"}
        result = {"target": backend["id"], "mongo": mongo["id"]}
        if mongo.get("health") != "healthy":
            return {**result, "reason": "mongo_unhealthy"}
        started = timestamp(backend["started_at"])
        if now - started < timedelta(minutes=15):
            return {**result, "reason": "startup_grace"}
        ready = local_http(run, backend["id"], "ready", 5)
        if ready is None:
            return {**result, "reason": "ready_unavailable"}
        body = ready["body"]
        if body.get("database") is False:
            return {**result, "reason": "mongo_unhealthy"}
        scheduler = body.get("scheduler", {})
        if (not isinstance(scheduler, dict) or type(scheduler.get("enabled")) is not bool
                or type(scheduler.get("running")) is not bool):
            return {**result, "reason": "probe_failed"}
        if scheduler.get("enabled") is False:
            return {**result, "reason": "maintenance"}
        if scheduler.get("running") is False:
            return {**result, "reason": "scheduler_stopped"}
        if ready.get("code") != 200 or body.get("database") is not True or body.get("status") != "ready":
            return {**result, "reason": "ready_unhealthy"}
        health = local_http(run, backend["id"], "pipeline/health", 12)
        jobs = (health or {}).get("body", {}).get("scheduler_jobs", {})
        if not health or health.get("code") != 200 or not isinstance(jobs, dict):
            return {**result, "reason": "probe_failed"}
        checked = timestamp(health["body"].get("checked_at"))
        received_at = clock()
        if not timedelta(0) <= received_at - checked <= timedelta(minutes=5):
            return {**result, "reason": "probe_failed"}
        if jobs.get("scheduler_state") in {"paused", "disabled"}:
            return {**result, "reason": "maintenance"}
        if jobs.get("scheduler_state") != "running":
            return {**result, "reason": "probe_failed"}
        entries = jobs.get("jobs")
        known = {"ok", "degraded", "blocked", "paused", "failed", "running", "stalled", "starting", "overdue", "unknown", "disabled"}
        if (not isinstance(entries, dict) or set(entries) != {"rss", "speed", "gpt"}
                or any(not isinstance(v, dict) or v.get("status") not in known
                       or type(v.get("current_boot")) is not bool for v in entries.values())):
            return {**result, "reason": "probe_failed"}
        if any(v.get("status") == "stalled" and not v["current_boot"] for v in entries.values()):
            return {**result, "reason": "probe_failed"}
        if any(v.get("status") == "stalled" and v.get("current_boot") is True for v in entries.values()):
            return {**result, "reason": "scheduler_job_stalled"}
        return {**result, "reason": "ready"}
    except Exception:
        return {"reason": "probe_failed"}


def initial_state():
    return {"version": 1, "target_id": None, "consecutive_failures": 0, "first_failure_at": None, "restart_attempts": []}


def load_state(path, now):
    if not path.exists():
        return initial_state()
    state = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(state, dict) or state.get("version") != 1
            or not isinstance(state.get("target_id"), (str, type(None)))
            or type(state.get("consecutive_failures")) is not int or state["consecutive_failures"] < 0
            or not isinstance(state.get("restart_attempts"), list)):
        raise ValueError("invalid state")
    for value in state["restart_attempts"]:
        if timestamp(value) > now + timedelta(minutes=1):
            raise ValueError("future attempt")
    first = state.get("first_failure_at")
    if ((state["consecutive_failures"] == 0 and first is not None)
            or (state["consecutive_failures"] > 0 and (first is None or timestamp(first) > now))):
        raise ValueError("invalid failure start")
    return state


def save_state(path, state):
    temporary = path.with_suffix(".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(state, handle, separators=(",", ":"))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    if os.name == "posix":
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def public_result(state, now, status, reason, action="none"):
    attempts = state.get("restart_attempts", [])
    return {"checked_at": stamp(now), "status": status, "action": action, "reason": reason,
            "consecutive_failures": state.get("consecutive_failures", 0),
            "restart_attempts_6h": len([t for t in attempts if timestamp(t) > now - timedelta(hours=6)]),
            "last_restart_at": max(attempts, key=timestamp) if attempts else None}


def observation_status(reason):
    if reason == "ready":
        return "healthy"
    if reason in {"maintenance", "deployment_active", "startup_grace"}:
        return "paused"
    return "error" if reason == "probe_failed" else "warning"


def publish(run, mongo_id, result):
    # Exactly one diagnostic document; never import application code or touch queues.
    document = json.dumps(result, separators=(",", ":"))
    script = "db.getSiblingDB('transfernews_db').ops_watchdog.replaceOne({_id:'host_watchdog'},Object.assign({_id:'host_watchdog'}," + document + "),{upsert:true})"
    run(["docker", "exec", mongo_id, "mongosh", "--quiet", "--eval", script], 8)


def tick(run, path, *, apply=False, now=None, maintenance=lambda: False, clock=None):
    clock = clock or utcnow
    now = now or clock()
    try:
        state = load_state(path, now)
    except Exception:
        return public_result(initial_state(), now, "error", "invalid_state")
    observed = observe(run, now, maintenance(), clock=clock)
    reason = observed["reason"]
    if observed.get("target") != state.get("target_id"):
        state["target_id"] = observed.get("target")
        state["consecutive_failures"] = 0
        state["first_failure_at"] = None
    if reason in RECOVERABLE:
        if not state["consecutive_failures"]:
            state["first_failure_at"] = stamp(now)
        state["consecutive_failures"] += 1
    else:
        state["consecutive_failures"] = 0
        state["first_failure_at"] = None
    result = public_result(state, now, observation_status(reason), reason)
    attempts = [timestamp(t) for t in state["restart_attempts"]]
    eligible = (reason in RECOVERABLE and state["consecutive_failures"] >= 3
                and now - timestamp(state["first_failure_at"]) >= timedelta(minutes=10))
    if eligible and sum(t > now - timedelta(hours=6) for t in attempts) >= 2:
        eligible = False
        result.update(reason="restart_budget_exhausted")
    elif eligible and attempts and now - max(attempts) < timedelta(minutes=30):
        eligible = False
        result.update(reason="cooldown")
    if eligible:
        # Fresh identity, helper/maintenance, startup, Mongo and HTTP checks immediately before action.
        current = observe(run, clock(), maintenance(), clock=clock)
        if current.get("target") != observed.get("target") or current.get("mongo") != observed.get("mongo"):
            result.update(status="paused", reason="target_changed")
            state["consecutive_failures"] = 0
            state["first_failure_at"] = None
        elif current["reason"] not in RECOVERABLE:
            result.update(status=observation_status(current["reason"]), reason=current["reason"])
            state["consecutive_failures"] = 0
            state["first_failure_at"] = None
        elif not apply:
            result.update(action="would_restart")
        else:
            state["restart_attempts"] = [stamp(t) for t in attempts if t > now - timedelta(hours=6)] + [stamp(now)]
            result = public_result(state, now, "recovering", reason, "restart_attempted")
            state["last_result"] = result
            try:
                save_state(path, state)  # A failed/ambiguous restart still consumes this budget.
            except Exception:
                return public_result(state, now, "error", "state_write_failed")
            try:
                run(["docker", "restart", "--time", "30", observed["target"]], 45)
                result["action"] = "restarted"  # Process command succeeded; not yet proof of readiness.
                state["consecutive_failures"] = 0
                state["first_failure_at"] = None
            except Exception:
                result.update(status="error", action="restart_failed", reason="restart_failed")
    result["consecutive_failures"] = state["consecutive_failures"]
    if apply:
        state["last_result"] = result
        try:
            save_state(path, state)
        except Exception:
            return public_result(state, now, "error", "state_write_failed")
        if observed.get("mongo") and reason not in {"mongo_unhealthy", "target_ambiguous", "deployment_active", "maintenance"}:
            try:
                publish(run, observed["mongo"], result)
            except Exception:
                # Local result remains authoritative; no recursive retries or recovery.
                if result["status"] == "healthy":
                    result.update(status="warning", reason="diagnostic_publish_failed")
                    state["last_result"] = result
                    try:
                        save_state(path, state)
                    except Exception:
                        result.update(status="error", reason="state_write_failed")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Persist diagnostics and permit bounded backend restarts")
    args = parser.parse_args()
    if not args.apply:
        print(json.dumps(tick(Runner(), ROOT / "state.json", maintenance=lambda: (ROOT / "maintenance").exists())))
        return
    import fcntl
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (ROOT / "lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps(public_result(initial_state(), utcnow(), "paused", "lock_busy")))
            return
        print(json.dumps(tick(Runner(), ROOT / "state.json", apply=True, maintenance=lambda: (ROOT / "maintenance").exists())))


if __name__ == "__main__":
    main()
