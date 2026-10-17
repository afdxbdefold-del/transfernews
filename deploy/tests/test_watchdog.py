"""Offline host watchdog contract: fake Docker only; isolated temporary state."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

spec = importlib.util.spec_from_file_location("watchdog", Path(__file__).parents[1] / "watchdog.py")
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
NOW = datetime(2026, 10, 17, 13, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def frozen_clock():
    with patch.object(w, "utcnow", return_value=NOW):
        yield


def container(service, identifier=None, **extra):
    return {"id": identifier or service + "-exact-id", "name": "/" + service + "-" + w.APP + "-release",
            "image": "transfernews:" + service, "running": True, "health": "healthy",
            "started_at": w.stamp(NOW - timedelta(hours=1)), "labels": {
                "com.docker.compose.project": w.APP, "com.docker.compose.service": service,
                "coolify.managed": "true"}, **extra}


class Docker:
    def __init__(self, ready=None, jobs=None):
        self.containers = [container("backend"), container("mongodb")]
        self.ready = ready or {"code": 200, "body": {"status": "ready", "database": True,
                     "scheduler": {"enabled": True, "running": True}}}
        default_jobs = {"scheduler_state": "running", "jobs": {key: {"status": "ok", "current_boot": True} for key in ("rss", "speed", "gpt")}}
        if jobs and isinstance(jobs.get("jobs"), dict):
            jobs = {**jobs, "jobs": {**default_jobs["jobs"], **jobs["jobs"]}}
            for item in jobs["jobs"].values(): item.setdefault("current_boot", True)
        self.health = {"code": 200, "body": {"checked_at": w.stamp(NOW), "scheduler_jobs": jobs or default_jobs, "provider": {"status": "blocked"},
                       "warnings": ["publication_stalled"]}}
        self.calls = []
        self.inventory_count = 0
        self.on_second_inventory = None
        self.restart_error = False

    def __call__(self, args, timeout=10):
        self.calls.append((args, timeout))
        if args[:3] == ["docker", "ps", "-aq"]:
            self.inventory_count += 1
            if self.inventory_count == 2 and self.on_second_inventory:
                self.on_second_inventory(self)
            return "\n".join(c["id"] for c in self.containers)
        if args[:2] == ["docker", "inspect"]:
            return "\n".join(json.dumps(c) for c in self.containers)
        if args[:2] == ["docker", "restart"]:
            if self.restart_error:
                raise subprocess.TimeoutExpired(args, timeout)
            return args[-1]
        if args[:2] == ["docker", "exec"] and args[3] == "python":
            if "/api/ready" in args[-1]:
                if self.ready == "timeout":
                    raise TimeoutError()
                return json.dumps(self.ready)
            return json.dumps(self.health)
        if args[:2] == ["docker", "exec"] and args[3] == "mongosh":
            return "{}"
        raise AssertionError("Unexpected command")

    def restarts(self):
        return [c for c, _ in self.calls if c[:2] == ["docker", "restart"]]


def state(path, failures=2, attempts=(), target="backend-exact-id"):
    value = {**w.initial_state(), "target_id": target, "consecutive_failures": failures,
             "first_failure_at": w.stamp(NOW - timedelta(minutes=10)) if failures else None,
             "restart_attempts": [w.stamp(t) for t in attempts]}
    path.write_text(json.dumps(value), encoding="utf-8")
    return value


def test_healthy_and_provider_block_do_not_restart(tmp_path):
    d = Docker()
    result = w.tick(d, tmp_path / "state.json", now=NOW)
    assert result["reason"] == "ready" and not d.restarts()
    assert not list(tmp_path.iterdir())
    assert all(c[0][:2] != ["docker", "restart"] and "mongosh" not in c[0] for c in d.calls)


def test_three_consecutive_failures_and_exact_target(tmp_path):
    path = tmp_path / "state.json"
    d = Docker("timeout")
    for n in range(3):
        result = w.tick(d, path, apply=True, now=NOW + timedelta(minutes=5*n))
        assert len(d.restarts()) == (1 if n == 2 else 0)
    assert result["status"] == "recovering"
    assert d.restarts() == [["docker", "restart", "--time", "30", "backend-exact-id"]]
    assert result["restart_attempts_6h"] == 1


def test_dry_run_never_changes_state_or_database(tmp_path):
    path = tmp_path / "state.json"
    state(path)
    before = path.read_bytes()
    d = Docker("timeout")
    assert w.tick(d, path, now=NOW)["action"] == "would_restart"
    assert path.read_bytes() == before and not d.restarts()
    assert not any("mongosh" in args for args, _ in d.calls)


@pytest.mark.parametrize("scenario", ["maintenance", "helper", "mongo", "startup", "ambiguous", "wrong_label", "disabled"])
def test_safety_stops(tmp_path, scenario):
    path = tmp_path / "state.json"
    state(path)
    d = Docker("timeout")
    if scenario == "helper":
        d.containers.append(container("helper", image="ghcr.io/coollabsio/coolify-helper:latest"))
    if scenario == "mongo":
        d.containers[1]["health"] = "unhealthy"
    if scenario == "startup":
        d.containers[0]["started_at"] = w.stamp(NOW - timedelta(minutes=14))
    if scenario == "ambiguous":
        d.containers.append(container("backend", identifier="other-backend"))
    if scenario == "wrong_label":
        d.containers[0]["labels"]["coolify.managed"] = "false"
    if scenario == "disabled":
        d.ready = {"code": 200, "body": {"scheduler": {"enabled": False, "running": False}}}
    result = w.tick(d, path, apply=True, now=NOW, maintenance=lambda: scenario == "maintenance")
    assert not d.restarts() and result["action"] == "none"


@pytest.mark.parametrize("status", ["overdue", "paused", "blocked", "failed", "unknown"])
def test_non_stalled_jobs_never_restart(tmp_path, status):
    path = tmp_path / "state.json"
    state(path)
    d = Docker(jobs={"scheduler_state": "running", "jobs": {"rss": {"status": status}}})
    assert w.tick(d, path, apply=True, now=NOW)["reason"] == "ready"
    assert not d.restarts()


def test_explicit_scheduler_stall_requires_running_scheduler(tmp_path):
    path = tmp_path / "state.json"
    state(path)
    d = Docker(jobs={"scheduler_state": "paused", "jobs": {"rss": {"status": "stalled"}}})
    assert w.tick(d, path, now=NOW)["reason"] == "maintenance"
    d.health["body"]["scheduler_jobs"]["scheduler_state"] = "running"
    assert w.tick(d, path, now=NOW)["action"] == "would_restart"


@pytest.mark.parametrize("change", ["target", "helper", "mongo", "recovered"])
def test_revalidate_immediately_before_restart(tmp_path, change):
    path = tmp_path / "state.json"
    state(path)
    d = Docker("timeout")
    def alter(fake):
        if change == "target": fake.containers[0]["id"] = "replacement-id"
        if change == "helper": fake.containers.append(container("helper", image="coollabsio/coolify-helper:latest"))
        if change == "mongo": fake.containers[1]["health"] = "unhealthy"
        if change == "recovered": fake.ready = Docker().ready
    d.on_second_inventory = alter
    result = w.tick(d, path, apply=True, now=NOW)
    assert not d.restarts() and result["action"] == "none"


def test_container_change_resets_failure_streak(tmp_path):
    path = tmp_path / "state.json"
    state(path, failures=100, target="old-id")
    result = w.tick(Docker("timeout"), path, now=NOW)
    assert result["consecutive_failures"] == 1 and result["action"] == "none"


@pytest.mark.parametrize("attempts,reason", [
    ([NOW-timedelta(minutes=20)], "cooldown"),
    ([NOW-timedelta(hours=2),NOW-timedelta(hours=1)], "restart_budget_exhausted"),
])
def test_budget_and_cooldown(tmp_path, attempts, reason):
    path = tmp_path / "state.json"
    state(path, attempts=attempts)
    d = Docker("timeout")
    assert w.tick(d, path, apply=True, now=NOW)["reason"] == reason
    assert not d.restarts()


def test_attempt_saved_before_ambiguous_restart_failure(tmp_path):
    path = tmp_path / "state.json"
    state(path)
    d = Docker("timeout")
    d.restart_error = True
    original = d.__call__
    def run(args, timeout):
        if args[:2] == ["docker", "restart"]:
            assert json.loads(path.read_text())["restart_attempts"] == [w.stamp(NOW)]
        return original(args, timeout)
    result = w.tick(run, path, apply=True, now=NOW)
    assert result["action"] == "restart_failed" and result["restart_attempts_6h"] == 1


def test_corrupt_state_fails_closed_without_commands_or_overwrite(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{broken", encoding="utf-8")
    d = Docker("timeout")
    result = w.tick(d, path, apply=True, now=NOW)
    assert result["reason"] == "invalid_state" and not d.calls
    assert path.read_text() == "{broken"


def test_budget_persistence_failure_prevents_restart(tmp_path):
    path = tmp_path / "state.json"
    state(path)
    d = Docker("timeout")
    with patch.object(w, "save_state", side_effect=OSError("disk full")):
        assert w.tick(d, path, apply=True, now=NOW)["reason"] == "state_write_failed"
    assert not d.restarts()


def test_only_sanitized_health_document_is_written(tmp_path):
    d = Docker()
    result = w.tick(d, tmp_path / "state.json", apply=True, now=NOW)
    writes = [args for args, _ in d.calls if "mongosh" in args]
    assert len(writes) == 1 and writes[0][2] == "mongodb-exact-id"
    assert "ops_watchdog.replaceOne({_id:'host_watchdog'}" in writes[0][-1]
    assert set(result) == {"checked_at","status","action","reason","consecutive_failures","restart_attempts_6h","last_restart_at"}
    assert result["status"] in w.STATUS and result["action"] in w.ACTIONS and result["reason"] in w.REASONS


def test_cli_lock_busy_does_not_probe_or_overwrite_state(tmp_path, capsys):
    path = tmp_path / "state.json"
    state(path)
    before = path.read_bytes()
    def busy(*args):
        raise BlockingIOError()
    fake = types.SimpleNamespace(LOCK_EX=1, LOCK_NB=2, flock=busy)
    with patch.dict(sys.modules, fcntl=fake), patch.object(w, "ROOT", tmp_path), \
            patch.object(sys, "argv", ["watchdog.py", "--apply"]), \
            patch.object(w, "Runner", side_effect=AssertionError("Must not probe")):
        w.main()
    assert json.loads(capsys.readouterr().out)["reason"] == "lock_busy"
    assert path.read_bytes() == before


def test_runner_bounds_each_command_by_remaining_total_deadline():
    with patch.object(w.time, "monotonic", return_value=100):
        runner = w.Runner()
    with patch.object(w.time, "monotonic", return_value=180), patch.object(w.subprocess, "run") as run:
        run.return_value.stdout = "ok"
        assert runner(["docker", "restart", "exact"], 45) == "ok"
        assert run.call_args.kwargs["timeout"] == 10
    with patch.object(w.time, "monotonic", return_value=191), patch.object(w.subprocess, "run") as run:
        with pytest.raises(TimeoutError):
            runner(["docker", "ps"], 8)
        run.assert_not_called()


def test_disabled_scheduler_even_on_failed_ready_is_not_restarted(tmp_path):
    path = tmp_path / "state.json"
    state(path)
    d = Docker({"code": 503, "body": {"database": False, "scheduler": {"enabled": False,"running":False}}})
    assert w.tick(d, path, apply=True, now=NOW)["reason"] == "mongo_unhealthy"
    assert not d.restarts()


def test_failed_diagnostic_publication_is_reported_locally(tmp_path):
    d = Docker()
    def run(args, timeout):
        if "mongosh" in args:
            raise TimeoutError()
        return d(args, timeout)
    result = w.tick(run, tmp_path / "state.json", apply=True, now=NOW)
    assert result["reason"] == "diagnostic_publish_failed"
    assert json.loads((tmp_path / "state.json").read_text())["last_result"] == result


def test_repeated_manual_calls_do_not_satisfy_ten_minute_failure_window(tmp_path):
    d = Docker("timeout")
    path = tmp_path / "state.json"
    for minute in range(5):
        result = w.tick(d, path, apply=True, now=NOW + timedelta(minutes=minute))
        assert not d.restarts()
    assert result["consecutive_failures"] == 5


@pytest.mark.parametrize("case", ["missing", "stale", "future", "naive", "bad_jobs", "stopped", "error_http"])
def test_invalid_health_signal_is_not_healthy_or_restarted(tmp_path, case):
    path = tmp_path / "state.json"
    state(path)
    d = Docker()
    if case == "missing": d.health["body"].pop("scheduler_jobs")
    if case == "stale": d.health["body"]["checked_at"] = w.stamp(NOW-timedelta(minutes=6))
    if case == "future": d.health["body"]["checked_at"] = w.stamp(NOW+timedelta(seconds=1))
    if case == "naive": d.health["body"]["checked_at"] = "2026-10-17T13:00:00"
    if case == "bad_jobs": d.health["body"]["scheduler_jobs"]["jobs"] = {"rss": {"status":"stalled"}}
    if case == "stopped": d.health["body"]["scheduler_jobs"]["scheduler_state"] = "stopped"
    if case == "error_http": d.health["code"] = 503
    result = w.tick(d, path, apply=True, now=NOW)
    assert result["reason"] == "probe_failed" and result["status"] != "healthy"
    assert not d.restarts()


def test_api_database_failure_does_not_restart_backend(tmp_path):
    path = tmp_path / "state.json"
    state(path)
    d = Docker()
    d.ready["body"]["database"] = False
    d.ready["code"] = 503
    assert w.tick(d, path, apply=True, now=NOW)["reason"] == "mongo_unhealthy"
    assert not d.restarts()


@pytest.mark.parametrize("snapshot_offset,expected", [(1, "ready"), (3, "probe_failed")])
def test_health_timestamp_is_compared_with_receipt_time_not_tick_start(tmp_path, snapshot_offset, expected):
    d = Docker()
    d.health["body"]["checked_at"] = w.stamp(NOW + timedelta(seconds=snapshot_offset))
    # The request starts at NOW. Its response is received two seconds later;
    # a newly generated snapshot at +1s is valid, one at +3s is truly future.
    clock = iter([NOW, NOW + timedelta(seconds=2)])
    result = w.tick(d, tmp_path / "state.json", clock=lambda: next(clock))
    assert result["reason"] == expected
    assert not d.restarts() and not list(tmp_path.iterdir())
