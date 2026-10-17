"""Offline throughput diagnostics: no application lifespan, Mongo server, or writes."""
from datetime import datetime, timedelta, timezone
import asyncio
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

import mongomock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline_health import PipelineHealthSnapshot, HealthWarningThrottle, collect_pipeline_health

NOW = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)


def fresh_event(**fields):
    return {"status": "review", "created_at": NOW - timedelta(minutes=5),
            "source_published_at": NOW - timedelta(hours=1), "processed_at": NOW - timedelta(minutes=3), **fields}


class HealthSnapshotTests(unittest.TestCase):
    def test_twenty_one_day_publication_gap_is_not_hidden_by_a_recent_draft(self):
        snapshot = PipelineHealthSnapshot(NOW)
        snapshot.add_event(fresh_event())
        snapshot.add_article({"status": "published", "published_at": NOW - timedelta(days=21)})
        snapshot.add_article({"status": "draft", "published_at": NOW, "rewrite_status": "review"})
        result = snapshot.result()
        self.assertEqual(result["warnings"], ["publication_stalled"])
        self.assertEqual(result["publication_gap_hours"], 504)
        self.assertEqual(result["activity"]["published_last_hour"], 0)
        self.assertEqual(result["stages"]["events"]["review"], 1)
        self.assertEqual(result["last_activity"]["processed_at"], (NOW - timedelta(minutes=3)).isoformat())
        self.assertFalse(result["readiness_impact"])

    def test_a_normal_news_pause_with_no_recent_ingestion_is_idle(self):
        snapshot = PipelineHealthSnapshot(NOW)
        snapshot.add_event(fresh_event(created_at=NOW - timedelta(days=3)))
        snapshot.add_article({"status": "published", "published_at": NOW - timedelta(days=4)})
        self.assertEqual(snapshot.result()["status"], "idle")
        self.assertEqual(snapshot.result()["warnings"], [])

    def test_old_feed_items_imported_now_are_not_fresh_input(self):
        snapshot = PipelineHealthSnapshot(NOW)
        snapshot.add_event(fresh_event(source_published_at=NOW - timedelta(days=300)))
        snapshot.add_event(fresh_event(source_published_at="broken"))
        snapshot.add_event(fresh_event(source_published_at=NOW + timedelta(days=1)))
        snapshot.add_article({"status": "published", "published_at": NOW - timedelta(days=21)})
        result = snapshot.result()
        self.assertEqual(result["activity"]["imports_last_24h"], 3)
        self.assertEqual(result["activity"]["fresh_imports_last_24h"], 0)
        self.assertEqual(result["warnings"], [])

    def test_new_installation_gets_a_full_day_before_missing_first_publication_warning(self):
        snapshot = PipelineHealthSnapshot(NOW)
        self.assertEqual(snapshot.result()["status"], "initializing")
        snapshot.add_event(fresh_event())
        self.assertEqual(snapshot.result()["status"], "initializing")
        self.assertEqual(snapshot.result()["warnings"], [])
        snapshot.add_event(fresh_event(created_at=NOW - timedelta(hours=24)))
        self.assertEqual(snapshot.result()["warnings"], ["publication_stalled"])

    def test_unknown_or_future_publication_time_is_reported_not_used_as_proof_of_progress(self):
        for value in (None, "invalid", NOW + timedelta(days=1), 12345):
            with self.subTest(value=value):
                snapshot = PipelineHealthSnapshot(NOW)
                snapshot.add_event(fresh_event())
                snapshot.add_article({"status": "published", "published_at": value})
                self.assertEqual(snapshot.result()["warnings"], ["publication_timestamp_unknown"])
                self.assertIsNone(snapshot.result()["last_activity"]["published_at"])

    def test_bson_naive_utc_and_iso_offsets_are_normalized_without_timestamp_string_ordering(self):
        snapshot = PipelineHealthSnapshot(NOW)
        snapshot.add_event(fresh_event(created_at=datetime(2026, 10, 17, 10, 0), processed_at="2026-10-17T13:30:00+02:00"))
        snapshot.add_article({"status": "published", "published_at": "2026-10-17T12:15:00+02:00"})
        snapshot.add_article({"status": "published", "published_at": "2026-10-17T11:15:00Z", "gpt_rewritten_at": "2026-10-17T11:14:00Z"})
        result = snapshot.result()
        self.assertEqual(result["last_activity"]["published_at"], "2026-10-17T11:15:00+00:00")
        self.assertEqual(result["last_activity"]["processed_at"], "2026-10-17T11:30:00+00:00")
        self.assertEqual(result["activity"]["published_last_hour"], 1)
        self.assertEqual(result["status"], "ok")

    def test_waiting_review_retry_and_failures_are_separate_in_each_stage(self):
        snapshot = PipelineHealthSnapshot(NOW)
        for state in ("pending", "retry", "processing", "review", "error", None):
            snapshot.add_event(fresh_event(status=state))
        for state in ("pending", "retry", "processing", "review", "failed", "blocked", "complete", None):
            snapshot.add_article({"status": "draft", "rewrite_status": state, "needs_gpt_rewrite": state not in ("review", "failed", "complete")})
        result = snapshot.result()
        self.assertEqual(result["stages"]["event_waiting"], 2)
        self.assertEqual(result["stages"]["events"]["unknown"], 1)
        self.assertEqual(result["stages"]["rewrite"]["waiting"], 3)
        self.assertEqual(result["stages"]["rewrite"]["pending"], 2)
        self.assertEqual(result["stages"]["rewrite"]["processing"], 1)
        self.assertEqual(result["stages"]["rewrite"]["review"], 1)
        self.assertEqual(result["stages"]["rewrite"]["failed"], 1)
        self.assertEqual(result["stages"]["rewrite"]["blocked"], 1)

    def test_provider_halt_is_visible_even_without_fresh_news_and_private_metadata_is_excluded(self):
        snapshot = PipelineHealthSnapshot(NOW)
        snapshot.add_provider({"status": "blocked", "error_code": "raw-secret-error", "error_kind": "billing",
                               "block_id": "private-id", "message": "raw-secret-error", "retry_at": NOW + timedelta(hours=1)})
        result = snapshot.result()
        self.assertEqual(result["warnings"], ["rewrite_provider_blocked"])
        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["provider"], {"status": "blocked", "error_code": "unknown", "error_kind": "billing", "retry_at": "2026-10-17T13:00:00+00:00"})
        self.assertNotIn("private-id", str(result))
        self.assertNotIn("raw-secret", str(result))
        self.assertFalse(result["readiness_impact"])

    def test_provider_safe_codes_are_retained_and_transient_retry_is_not_a_persistent_halt(self):
        snapshot = PipelineHealthSnapshot(NOW)
        snapshot.add_provider({"status": "retry", "error_code": "rate_limit_exceeded", "error_kind": "rate_limit", "retry_at": NOW + timedelta(minutes=1)})
        self.assertEqual(snapshot.result()["provider"]["error_code"], "rate_limit_exceeded")
        self.assertEqual(snapshot.result()["warnings"], [])
        snapshot.add_provider({"status": "blocked", "error_code": "insufficient_quota", "error_kind": "billing"})
        self.assertEqual(snapshot.result()["provider"]["error_code"], "insufficient_quota")
        self.assertEqual(snapshot.result()["warnings"], ["rewrite_provider_blocked"])

    def test_existing_articles_without_events_are_idle_not_unknown(self):
        snapshot = PipelineHealthSnapshot(NOW)
        snapshot.add_article({"status": "published", "published_at": NOW})
        self.assertEqual(snapshot.result()["status"], "idle")

    def test_backlog_warning_and_missing_old_timestamps_are_explicit(self):
        snapshot = PipelineHealthSnapshot(NOW)
        for _ in range(51):
            snapshot.add_event({"status": "pending"})
        result = snapshot.result()
        self.assertEqual(result["warnings"], ["event_backlog"])
        self.assertEqual(result["data_quality"]["events_without_valid_import_time"], 51)
        self.assertIsNone(result["last_activity"]["imported_at"])

    def test_warnings_are_throttled_and_recovery_then_new_episode_are_not_suppressed(self):
        throttle = HealthWarningThrottle()
        self.assertEqual(throttle.update(["publication_stalled"], NOW), (["publication_stalled"], []))
        for minutes in (5, 10, 60, 359):
            self.assertEqual(throttle.update(["publication_stalled"], NOW + timedelta(minutes=minutes)), ([], []))
        self.assertEqual(throttle.update(["publication_stalled"], NOW + timedelta(hours=6)), (["publication_stalled"], []))
        self.assertEqual(throttle.update([], NOW + timedelta(hours=6, minutes=5)), ([], ["publication_stalled"]))
        self.assertEqual(throttle.update([], NOW + timedelta(hours=6, minutes=10)), ([], []))
        self.assertEqual(throttle.update(["publication_stalled"], NOW + timedelta(hours=6, minutes=15)), (["publication_stalled"], []))

    def test_failed_read_does_not_claim_previous_publication_warning_recovered(self):
        throttle = HealthWarningThrottle()
        throttle.update(["publication_stalled"], NOW)
        self.assertEqual(throttle.update(["diagnostic_unavailable"], NOW + timedelta(minutes=5), complete=False), (["diagnostic_unavailable"], []))
        self.assertEqual(throttle.update(["publication_stalled"], NOW + timedelta(minutes=10)), ([], ["diagnostic_unavailable"]))


class ProjectedCollection:
    """Only find is exposed: a diagnostic mutation would fail this test."""
    def __init__(self, collection):
        self.collection = collection
        self.projections = []

    def find(self, query, projection):
        self.projections.append(projection)
        async def records():
            for record in self.collection.find(query, projection):
                yield record
        return records()

    async def find_one(self, query, projection):
        self.projections.append(projection)
        return self.collection.find_one(query, projection)


class HealthCollectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_scheduler_cancels_a_stuck_diagnostic_and_returns_a_sanitized_warning(self):
        import scheduler
        cancelled = asyncio.Event()
        async def stuck(_db):
            try:
                await asyncio.Future()
            finally:
                cancelled.set()
        with patch.object(scheduler, "HEALTH_CHECK_TIMEOUT_SECONDS", 0.01), \
             patch.object(scheduler, "_health_warnings", HealthWarningThrottle()), \
             patch.object(scheduler, "get_db", return_value=None), \
             patch.object(scheduler, "collect_pipeline_health", stuck), \
             patch.object(scheduler.logger, "warning") as warning:
            result = await scheduler.task_health_check()
        self.assertTrue(cancelled.is_set())
        self.assertEqual(result["warnings"], ["diagnostic_unavailable"])
        self.assertFalse(result["readiness_impact"])
        self.assertEqual(warning.call_count, 1)
        self.assertFalse(scheduler.scheduler.running)

    async def test_collector_is_read_only_and_does_not_fetch_or_expose_article_text(self):
        raw = mongomock.MongoClient().diagnostics
        raw.events.insert_one({**fresh_event(), "body_raw": "secret source body"})
        raw.articles.insert_one({"status": "published", "published_at": NOW.isoformat(), "body": "secret article body"})
        db = type("ReadOnlyDB", (), {})()
        db.events = ProjectedCollection(raw.events)
        db.articles = ProjectedCollection(raw.articles)
        db.rewrite_provider_state = ProjectedCollection(raw.rewrite_provider_state)
        result = await collect_pipeline_health(db, NOW)
        self.assertEqual(result["status"], "ok")
        self.assertNotIn("secret", str(result))
        self.assertNotIn("body_raw", db.events.projections[0])
        self.assertNotIn("body", db.articles.projections[0])
        self.assertEqual(raw.events.count_documents({}), 1)

    async def test_scheduler_returns_sanitized_diagnostic_failure_once_without_starting_jobs(self):
        import scheduler
        self.assertFalse(scheduler.scheduler.running)
        throttle = HealthWarningThrottle()
        with patch.object(scheduler, "_health_warnings", throttle), \
             patch.object(scheduler, "get_db", return_value=None), \
             patch.object(scheduler, "collect_pipeline_health", AsyncMock(side_effect=RuntimeError("secret-connection-string"))), \
             patch.object(scheduler.logger, "warning") as warning:
            first = await scheduler.task_health_check()
            second = await scheduler.task_health_check()
        self.assertEqual(first["warnings"], ["diagnostic_unavailable"])
        self.assertEqual(second["status"], "unknown")
        self.assertNotIn("secret", str(first))
        self.assertNotIn("secret", str(warning.call_args))
        self.assertEqual(warning.call_count, 1)
        self.assertFalse(scheduler.scheduler.running)


if __name__ == "__main__":
    unittest.main()
