import importlib.util
from pathlib import Path
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("public_monitor", Path(__file__).parents[1] / "public_monitor.py")
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class PublicMonitorTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.ready = {"status": "ready", "database": True, "scheduler": {"enabled": True, "running": True}}
        self.health = {"status": "ok", "warnings": [], "checked_at": self.now.isoformat(),
                       "scheduler_jobs": {"status": "ok"},
                       "watchdog": {"status": "healthy", "checked_at": self.now.isoformat()}}

    def test_success_and_editorially_idle_are_healthy(self):
        self.assertEqual(monitor.assess(self.ready, self.health, self.now), [])
        self.health["status"] = "idle"
        self.assertEqual(monitor.assess(self.ready, self.health, self.now), [])

    def test_http_success_cannot_hide_stalled_publication(self):
        self.health["warnings"] = ["publication_stalled"]
        self.assertIn("pipeline_requires_attention", monitor.assess(self.ready, self.health, self.now))

    def test_missing_run_or_watchdog_evidence_fails(self):
        del self.health["scheduler_jobs"]
        del self.health["watchdog"]
        errors = monitor.assess(self.ready, self.health, self.now)
        self.assertIn("scheduler_runs_not_verified", errors)
        self.assertIn("host_watchdog_not_current", errors)

    def test_stale_and_future_watchdog_fails(self):
        for when in (self.now - timedelta(minutes=21), self.now + timedelta(minutes=1)):
            self.health["watchdog"]["checked_at"] = when.isoformat()
            self.assertIn("host_watchdog_not_current", monitor.assess(self.ready, self.health, self.now))

    def test_disabled_scheduler_fails(self):
        self.ready["scheduler"]["enabled"] = False
        self.assertIn("application_not_ready", monitor.assess(self.ready, self.health, self.now))

    def test_restart_grace_needs_current_scheduler_epoch(self):
        self.health["watchdog"].update(status="paused", reason="startup_grace")
        self.assertIn("host_watchdog_requires_attention", monitor.assess(self.ready, self.health, self.now))
        self.health["scheduler_jobs"]["started_at"] = self.now.isoformat()
        self.assertEqual(monitor.assess(self.ready, self.health, self.now), [])
        self.health["scheduler_jobs"]["started_at"] = (self.now - timedelta(minutes=16)).isoformat()
        self.assertIn("host_watchdog_requires_attention", monitor.assess(self.ready, self.health, self.now))

    def test_transient_failure_gets_one_recheck(self):
        with patch.object(monitor, "check_once", side_effect=[["public_request_failed"], []]) as call, patch.object(monitor.time, "sleep"):
            self.assertEqual(monitor.main(), 0)
            self.assertEqual(call.call_count, 2)

    def test_repeat_failure_is_nonzero(self):
        with patch.object(monitor, "check_once", return_value=["public_request_failed"]), patch.object(monitor.time, "sleep"):
            self.assertEqual(monitor.main(), 1)


if __name__ == "__main__":
    unittest.main()
