"""Offline scheduler evidence: fake Mongo, no jobs started and no external I/O."""
import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

import mongomock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scheduler_runs as runs

NOW = datetime(2026, 10, 17, 13, tzinfo=timezone.utc)


def runtime(**changes):
    return {"boot_id": "current", "started_at": NOW, "enabled": True,
            "scheduler_state": "running", "recording_errors": {}, **changes}


def record(job="rss", **changes):
    return {"_id": job, "boot_id": "current", "state": "finished",
            "last_started_at": NOW, "last_finished_at": NOW,
            "last_success_at": NOW, "last_outcome": "ok", "counts": {}, **changes}


class Collection:
    def __init__(self):
        self.raw = mongomock.MongoClient().test.runs
        self.hook = None

    async def update_one(self, query, update, **kwargs):
        if self.hook:
            await self.hook(query, update)
        return self.raw.update_one(query, update, **kwargs)

    def find(self, query, projection):
        async def records():
            for row in self.raw.find(query, projection):
                yield row
        return records()


@pytest.mark.parametrize("job,result,outcome,error", [
    ("rss", {"new_events": 0, "feeds_checked": 14, "feed_errors": {}}, "ok", None),
    ("rss", {"feeds_checked": 14, "feed_errors": {"secret-url": "private-error"}}, "degraded", "partial_feed_failure"),
    ("rss", {"feeds_checked": 1, "feed_errors": {"secret-url": "private-error"}}, "failed", "all_feeds_failed"),
    ("rss", {"feeds_checked": 0}, "failed", "no_active_feeds"),
    ("speed", {"processed": 0, "errors": []}, "ok", None),
    ("speed", {"processed": 20, "review": 20}, "ok", None),
    ("speed", {"retry": 1, "errors": ["private-error"]}, "degraded", "processing_errors"),
    ("gpt", {"rewritten": 0, "rejected": 2}, "ok", None),
    ("gpt", {"blocked": "private-error", "errors": 1}, "blocked", "provider_blocked"),
    ("gpt", {"paused": "private-error"}, "paused", None),
    ("gpt", {"errors": 1}, "degraded", "rewrite_errors"),
    ("gpt", {"error": "private-error"}, "failed", "task_reported_error"),
    ("gpt", None, "failed", "invalid_result"),
])
def test_only_fixed_outcomes_and_numeric_counts_are_retained(job, result, outcome, error):
    actual = runs.classify_job_result(job, result)
    assert actual[:2] == (outcome, error)
    assert "private" not in str(actual)
    assert "secret-url" not in str(actual)


def test_missing_new_boot_has_start_grace_then_overdue_never_stalled():
    old = record(state="running", boot_id="previous", last_started_at=NOW - timedelta(days=1))
    first = runs.summarize_scheduler_runs([old], NOW, runtime())
    assert first["jobs"]["rss"]["status"] == "starting"
    assert first["jobs"]["rss"]["current_boot"] is False
    later = runs.summarize_scheduler_runs([old], NOW + timedelta(minutes=7), runtime())
    assert {j["status"] for j in later["jobs"].values()} == {"overdue"}
    assert "stalled" not in str(later)


@pytest.mark.parametrize("job", ["rss", "speed", "gpt"])
def test_stalled_requires_current_running_job_over_full_workload_budget(job):
    limit = runs.JOB_CONFIG[job]["max_runtime_seconds"]
    active = record(job, state="running")
    assert runs.summarize_scheduler_runs([active], NOW + timedelta(seconds=limit), runtime())["jobs"][job]["status"] == "running"
    assert runs.summarize_scheduler_runs([active], NOW + timedelta(seconds=limit + 1), runtime())["jobs"][job]["status"] == "stalled"
    active["state"] = "finished"
    assert runs.summarize_scheduler_runs([active], NOW + timedelta(seconds=limit + 1), runtime())["jobs"][job]["status"] != "stalled"


def test_paused_disabled_and_failed_observation_never_recommend_restart():
    active = record(state="running", last_started_at=NOW - timedelta(days=1))
    for context, expected in ((runtime(scheduler_state="paused"), "paused"),
                              (runtime(enabled=False), "disabled"),
                              (runtime(recording_errors={"rss": "finish_record_failed"}), "unknown")):
        result = runs.summarize_scheduler_runs([active], NOW, context)
        assert result["jobs"]["rss"]["status"] == expected
        assert "stalled" not in str(result)


def test_zero_work_success_stays_healthy_without_any_news_records():
    result = runs.summarize_scheduler_runs([record(job) for job in runs.JOB_CONFIG], NOW + timedelta(seconds=30), runtime())
    assert result["status"] == "ok"
    assert result["warnings"] == []
    assert all(job["last_success_at"] == NOW.isoformat() for job in result["jobs"].values())


def test_public_projection_drops_tokens_errors_and_arbitrary_metadata():
    row = record(run_id="secret-run", api_key="secret-key", last_error_code="private-error",
                 counts={"feeds_checked": 14, "body": "private-body"})
    result = runs.summarize_scheduler_runs([row], NOW, runtime())
    assert not any(value in json.dumps(result) for value in ("secret", "private", "current" + '"'))
    assert result["jobs"]["rss"]["last_error_code"] is None


class RecordedJobTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = SimpleNamespace(pipeline_job_runs=Collection())
        self.patch_context = patch.object(runs, "runtime_context", return_value=runtime())
        self.patch_context.start()
        self.addCleanup(self.patch_context.stop)
        self.clock = patch.object(runs, "utcnow", return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        runs._recording_errors.clear()

    async def test_each_empty_queue_records_real_successful_finish(self):
        for job, value in (("rss", {"feeds_checked": 14, "new_events": 0}),
                           ("speed", {"processed": 0}), ("gpt", {"rewritten": 0})):
            operation = AsyncMock(return_value=value)
            self.assertEqual(await runs.run_scheduled_job(self.db, job, operation), value)
            saved = self.db.pipeline_job_runs.raw.find_one({"_id": job})
            self.assertEqual(saved["state"], "finished")
            self.assertEqual(saved["last_outcome"], "ok")
            self.assertEqual(saved["last_success_at"], NOW.replace(tzinfo=None))
            self.assertNotIn("run_id", saved)

    async def test_provider_block_finishes_and_never_claims_success(self):
        await runs.run_scheduled_job(self.db, "gpt", AsyncMock(return_value={"blocked": "secret-provider-response"}))
        saved = self.db.pipeline_job_runs.raw.find_one({"_id": "gpt"})
        self.assertEqual(saved["last_outcome"], "blocked")
        self.assertIn("last_finished_at", saved)
        self.assertNotIn("last_success_at", saved)
        self.assertNotIn("secret", str(saved))

    async def test_exception_text_is_never_logged_or_persisted(self):
        with self.assertLogs("scheduler_runs", level="WARNING") as logs:
            result = await runs.run_scheduled_job(self.db, "speed", AsyncMock(side_effect=RuntimeError("secret-password")))
        self.assertEqual(result, {"error": "job_exception"})
        self.assertNotIn("secret", str(logs.output))
        self.assertNotIn("secret", str(self.db.pipeline_job_runs.raw.find_one({})))

    async def test_cancellation_records_no_success_and_propagates(self):
        entered = asyncio.Event()
        async def pending():
            entered.set()
            await asyncio.Future()
        task = asyncio.create_task(runs.run_scheduled_job(self.db, "rss", pending))
        await entered.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        saved = self.db.pipeline_job_runs.raw.find_one({"_id": "rss"})
        self.assertEqual(saved["state"], "finished")
        self.assertEqual(saved["last_outcome"], "cancelled")
        self.assertEqual(saved["last_error_code"], "job_cancelled")
        self.assertNotIn("last_success_at", saved)

    async def test_late_first_finish_cannot_overwrite_newer_run(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def first():
            entered.set()
            await release.wait()
            return {"processed": 1}
        old = asyncio.create_task(runs.run_scheduled_job(self.db, "speed", first))
        await entered.wait()
        await runs.run_scheduled_job(self.db, "speed", AsyncMock(return_value={"processed": 2}))
        release.set()
        await old
        self.assertEqual(self.db.pipeline_job_runs.raw.find_one({"_id": "speed"})["counts"]["processed"], 2)

    async def test_recording_timeout_does_not_hold_or_stop_editorial_work(self):
        async def stuck(*args):
            await asyncio.Future()
        self.db.pipeline_job_runs.hook = stuck
        operation = AsyncMock(return_value={"processed": 0})
        with patch.object(runs, "RECORD_TIMEOUT_SECONDS", 0.01):
            await runs.run_scheduled_job(self.db, "speed", operation)
        operation.assert_awaited_once()
        self.assertEqual(runs._recording_errors["speed"], "start_record_failed")

    async def test_finish_recording_error_is_unknown_not_a_restartable_hang(self):
        async def fail_finish(query, update):
            if update["$set"].get("state") == "finished":
                raise RuntimeError("secret-mongo-error")
        self.db.pipeline_job_runs.hook = fail_finish
        await runs.run_scheduled_job(self.db, "rss", AsyncMock(return_value={"feeds_checked": 14}))
        row = self.db.pipeline_job_runs.raw.find_one({})
        result = runs.summarize_scheduler_runs([row], NOW + timedelta(hours=2), runtime(recording_errors=runs._recording_errors))
        self.assertEqual(result["jobs"]["rss"]["status"], "unknown")

    async def test_only_regular_registration_wrapper_records_cron_execution(self):
        import scheduler
        fake_scheduler = SimpleNamespace(add_job=Mock())
        with patch.object(scheduler, "scheduler", fake_scheduler):
            scheduler.setup_scheduler()
        registrations = {call.kwargs["id"]: call for call in fake_scheduler.add_job.call_args_list}
        for job_id in ("rss_scrape", "speed_pipeline", "gpt_rewrite"):
            self.assertIs(registrations[job_id].args[0], scheduler._scheduled_task)
        with patch.object(scheduler, "task_rss_scrape", AsyncMock(return_value={"new_events": 0})), \
             patch.object(scheduler, "run_scheduled_job", AsyncMock()) as recorder:
            await scheduler.trigger_rss_scrape()
            recorder.assert_not_called()
        self.assertEqual(self.db.pipeline_job_runs.raw.count_documents({}), 0)


if __name__ == "__main__":
    unittest.main()
