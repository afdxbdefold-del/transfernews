"""Offline regression for billing stops, shared backoff and operator release."""
import asyncio
from datetime import timedelta
from email.utils import format_datetime
import os
from pathlib import Path
import socket
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

import httpx
import openai

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline_state import utcnow
from rewrite_errors import (BILLING_CODES, PROVIDER_ID, classify_rewrite_error,
                            get_rewrite_provider_pause, resume_rewrite_provider,
                            record_rewrite_provider_failure, record_rewrite_provider_success)
from speed_pipeline import GPTRewriter, SpeedPipeline
from test_pipeline_repair import Database


def api_error(status, code, headers=None):
    response = httpx.Response(status, headers=headers, request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"))
    cls = openai.RateLimitError if status == 429 else (openai.AuthenticationError if status == 401 else openai.APIStatusError)
    return cls("NEVER_LOG_SENTINEL_message", response=response,
               body={"code": code, "message": "NEVER_LOG_SENTINEL_body", "type": "api_error"})


class ErrorClassificationTests(unittest.TestCase):
    def test_all_billing_codes_are_blocked(self):
        for code in BILLING_CODES:
            with self.subTest(code=code):
                failure = classify_rewrite_error(api_error(429, code))
                self.assertEqual((failure.code, failure.kind, failure.blocked), (code, "billing", True))

    def test_transient_retry_after_and_http_dates(self):
        now = utcnow().replace(microsecond=0)
        for code in ("rate_limit_exceeded", "slow_down"):
            failure = classify_rewrite_error(api_error(429, code, {"Retry-After": "900"}), now)
            self.assertEqual((failure.blocked, failure.retry_after), (False, 900))
        failure = classify_rewrite_error(api_error(503, "server_is_overloaded", {
            "Retry-After": format_datetime(now + timedelta(minutes=20), usegmt=True)}), now)
        self.assertEqual(failure.retry_after, 1200)

    def test_codes_never_copy_untrusted_provider_text(self):
        for status in (400, 401, 403, 429, 503):
            failure = classify_rewrite_error(api_error(status, "NEVER_LOG_SENTINEL_code"))
            self.assertNotIn("NEVER_LOG_SENTINEL", str(failure))
        self.assertTrue(classify_rewrite_error(api_error(429, None)).blocked)
        self.assertFalse(classify_rewrite_error(TimeoutError()).blocked)
        self.assertIsNone(classify_rewrite_error(ValueError("NEVER_LOG_SENTINEL")))

    def test_legacy_quota_type_and_malformed_headers(self):
        error = api_error(429, None)
        error.type = "insufficient_quota"
        self.assertEqual(classify_rewrite_error(error).code, "insufficient_quota")
        for value in ("nonsense", "-10", "inf", "nan"):
            self.assertEqual(classify_rewrite_error(api_error(429, "slow_down", {"Retry-After": value})).retry_after, 0)


class ProviderQueueTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = Database()
        self.pipeline = SpeedPipeline(self.db)
        self.pipeline._assign_article_image = AsyncMock()
        self.env = patch.dict(os.environ, {"OPENAI_API_KEY": "offline-fixture"})
        self.env.start()
        self.addCleanup(self.env.stop)
        network = patch.object(socket.socket, "connect", side_effect=AssertionError("No network allowed"))
        network.start()
        self.addCleanup(network.stop)
        await self.pipeline.process_event({"id": "event", "status": "pending", "created_at": utcnow(),
            "source_published_at": utcnow(), "headline_raw": "Arsenal may move for Endrick in January",
            "summary": "", "source_name": "BBC Sport", "source_url": "https://www.bbc.com/sport/football/articles/test"})
        original = await self.db.articles.find_one({})
        for i in range(1, 4):
            clone = {**original, "id": f"other-{i}", "slug": f"other-{i}"}
            clone.pop("_id")
            await self.db.articles.insert_one(clone)
        self.before = await self.db.articles.find_one({"id": original["id"]})
        self.client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(
            create=AsyncMock())), close=AsyncMock())

    async def run_failure(self, error):
        self.client.chat.completions.create.side_effect = error
        with patch("openai.AsyncOpenAI", return_value=self.client) as factory:
            result = await GPTRewriter(self.db).process_rewrite_queue(5)
        factory.assert_called_once_with(api_key="offline-fixture", timeout=60, max_retries=0)
        return result

    async def test_quota_halts_first_call_and_survives_new_worker_without_logging_secrets(self):
        with self.assertLogs("speed_pipeline", level="WARNING") as logs:
            result = await self.run_failure(api_error(429, "credit_balance_exhausted"))
        self.assertNotIn("NEVER_LOG_SENTINEL", "\n".join(logs.output))
        self.assertEqual(result["blocked"], "credit_balance_exhausted")
        self.assertEqual(self.client.chat.completions.create.await_count, 1)
        for _ in range(2):
            with patch("openai.AsyncOpenAI") as factory:
                later = await GPTRewriter(self.db).process_rewrite_queue(5)
                factory.assert_not_called()
            self.assertEqual(later["blocked"], result["blocked"])
        state = await get_rewrite_provider_pause(self.db)
        self.assertEqual(state["status"], "blocked")
        self.assertNotIn("NEVER_LOG_SENTINEL", str(state))
        blocked = await self.db.articles.find_one({"rewrite_status": "blocked"})
        self.assertTrue(blocked["needs_gpt_rewrite"])
        self.assertEqual(blocked["rewrite_last_error"], "credit_balance_exhausted")
        self.assertNotIn("rewrite_token", blocked)
        self.assertNotIn("rewrite_lease_until", blocked)
        self.assertEqual(blocked["body"], self.before["body"])
        self.assertEqual(blocked["content_revision"], self.before["content_revision"])
        self.assertEqual(blocked["status"], "draft")
        self.assertEqual(await self.db.articles.count_documents({"rewrite_attempts": 1}), 1)

    async def test_auth_failure_is_visible_and_requires_operator(self):
        result = await self.run_failure(api_error(401, "invalid_api_key"))
        self.assertEqual(result["blocked"], "invalid_api_key")
        state = await get_rewrite_provider_pause(self.db)
        with self.assertRaises(ValueError):
            await resume_rewrite_provider(self.db, expected_block_id=state["block_id"])
        stale = await resume_rewrite_provider(self.db, expected_block_id="wrong", operator_confirmed=True)
        self.assertFalse(stale["resumed"])
        before = list(self.db.articles.raw.find({}))
        released = await resume_rewrite_provider(self.db, expected_block_id=state["block_id"], operator_confirmed=True)
        self.assertEqual(released, {"resumed": True, "requeued_articles": 0})
        self.assertIsNone(await get_rewrite_provider_pause(self.db))
        self.assertEqual(before, list(self.db.articles.raw.find({})))

    async def test_transient_delay_prevents_other_article_calls_and_recovers(self):
        now = utcnow()
        result = await self.run_failure(api_error(429, "slow_down", {"Retry-After": "900"}))
        self.assertEqual(result["paused"], "slow_down")
        article = await self.db.articles.find_one({"rewrite_status": "retry"})
        self.assertGreaterEqual(article["rewrite_next_attempt_at"], now + timedelta(seconds=900))
        self.assertEqual(self.client.chat.completions.create.await_count, 1)
        with patch("openai.AsyncOpenAI") as factory:
            self.assertEqual((await GPTRewriter(self.db).process_rewrite_queue())["paused"], "slow_down")
            factory.assert_not_called()
        later = now + timedelta(minutes=16)
        self.client.chat.completions.create.side_effect = None
        self.client.chat.completions.create.return_value = types.SimpleNamespace(choices=[types.SimpleNamespace(
            message=types.SimpleNamespace(content="## Endrick im Gespräch\nBBC Sport berichtet, dass Arsenal im Januar einen Vorstoß für Endrick erwägen könnte. Die Gerüchtemeldung beschreibt eine mögliche Entwicklung und keinen bestätigten Wechsel."))])
        with patch("rewrite_errors.utcnow", return_value=later), patch("speed_pipeline.utcnow", return_value=later), patch("openai.AsyncOpenAI", return_value=self.client):
            result = await GPTRewriter(self.db).process_rewrite_queue(1)
        self.assertEqual(result["rewritten"], 1)
        self.assertIsNone(await get_rewrite_provider_pause(self.db))

    async def test_five_transient_provider_failures_stop_instead_of_infinite_retry(self):
        first = utcnow()
        for attempt in range(5):
            when = first + timedelta(hours=attempt * 2)
            with patch("rewrite_errors.utcnow", return_value=when), patch("speed_pipeline.utcnow", return_value=when):
                result = await self.run_failure(api_error(503, "server_is_overloaded"))
        self.assertEqual(result["blocked"], "server_is_overloaded")
        state = await get_rewrite_provider_pause(self.db)
        self.assertTrue(state["retry_exhausted"])
        self.assertEqual(state["consecutive_failures"], 5)
        self.assertNotIn("retry_at", state)
        self.assertEqual(self.client.chat.completions.create.await_count, 5)

    async def test_billing_failure_on_validation_retry_never_publishes(self):
        invalid = types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="too short"))])
        self.client.chat.completions.create.side_effect = [invalid, api_error(429, "insufficient_quota")]
        with patch("openai.AsyncOpenAI", return_value=self.client):
            result = await GPTRewriter(self.db).process_rewrite_queue()
        self.assertEqual(result["blocked"], "insufficient_quota")
        self.assertEqual(self.client.chat.completions.create.await_count, 2)
        self.assertEqual(await self.db.articles.count_documents({"status": "published"}), 0)
        saved = await self.db.articles.find_one({"rewrite_status": "blocked"})
        self.assertEqual(saved["body"], self.before["body"])

    async def test_timeout_and_server_error_are_scheduled_not_silent_failed(self):
        for error in (openai.APITimeoutError(request=httpx.Request("POST", "https://api.openai.com")), api_error(500, None)):
            self.db.rewrite_provider_state.raw.delete_many({})
            self.db.articles.raw.update_many({}, {"$unset": {"rewrite_next_attempt_at": ""}})
            result = await self.run_failure(error)
            self.assertIn("paused", result)
            self.assertEqual(await self.db.articles.count_documents({"rewrite_status": "failed"}), 0)

    async def test_new_revision_is_not_overwritten_by_failed_older_request(self):
        async def fail(**_):
            await self.db.articles.update_one({"id": self.before["id"]}, {
                "$set": {"content_revision": self.before["content_revision"] + 1, "body": "new-source"},
                "$unset": {"rewrite_token": "", "rewrite_lease_until": ""}})
            raise api_error(429, "insufficient_quota")
        self.client.chat.completions.create.side_effect = fail
        with patch("openai.AsyncOpenAI", return_value=self.client):
            await GPTRewriter(self.db).process_rewrite_queue()
        saved = await self.db.articles.find_one({"id": self.before["id"]})
        self.assertEqual(saved["body"], "new-source")
        self.assertNotEqual(saved["rewrite_status"], "blocked")
        self.assertEqual(self.client.chat.completions.create.await_count, 1)

    async def test_concurrent_workers_do_not_both_call_a_blocked_provider(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def fail(**_):
            entered.set()
            await release.wait()
            raise api_error(429, "insufficient_quota")
        self.client.chat.completions.create.side_effect = fail
        with patch("openai.AsyncOpenAI", return_value=self.client):
            first = asyncio.create_task(GPTRewriter(self.db).process_rewrite_queue())
            await entered.wait()
            second = await GPTRewriter(self.db).process_rewrite_queue()
            release.set()
            await first
        self.assertEqual(second["paused"], "provider_busy")
        self.assertEqual(self.client.chat.completions.create.await_count, 1)

    async def test_stale_pending_source_is_reviewed_without_any_provider_request(self):
        self.db.articles.raw.update_many({}, {"$set": {"source_published_at": utcnow() - timedelta(days=30)}})
        with patch("openai.AsyncOpenAI", return_value=self.client):
            result = await GPTRewriter(self.db).process_rewrite_queue()
        self.client.chat.completions.create.assert_not_awaited()
        self.assertEqual(result["rejected"], 4)
        self.assertEqual(await self.db.articles.count_documents({
            "rewrite_status": "review", "rewrite_review_reason": "source_not_fresh", "needs_gpt_rewrite": False}), 4)
        saved = await self.db.articles.find_one({"id": self.before["id"]})
        self.assertEqual(saved["body"], self.before["body"])
        self.assertEqual(saved["content_revision"], self.before["content_revision"])
        self.assertEqual(saved["published_at"], self.before["published_at"])
        self.assertNotIn("rewrite_token", saved)


class ProviderStateRaceTests(unittest.IsolatedAsyncioTestCase):
    async def test_stale_timeout_cannot_replace_concurrent_billing_block(self):
        for initially_missing in (True, False):
            with self.subTest(initially_missing=initially_missing):
                db = Database()
                if not initially_missing:
                    await record_rewrite_provider_success(db, None)
                real = db.rewrite_provider_state
                entered, release = asyncio.Event(), asyncio.Event()

                class PausedRead:
                    first = True

                    async def find_one(self, *args, **kwargs):
                        value = await real.find_one(*args, **kwargs)
                        if self.first:
                            self.first = False
                            entered.set()
                            await release.wait()
                        return value

                    def __getattr__(self, key):
                        return getattr(real, key)

                racing = types.SimpleNamespace(rewrite_provider_state=PausedRead())
                stale_timeout = asyncio.create_task(record_rewrite_provider_failure(
                    racing, classify_rewrite_error(TimeoutError())))
                await entered.wait()
                blocked = await record_rewrite_provider_failure(db, classify_rewrite_error(api_error(429, "insufficient_quota")))
                release.set()
                result = await stale_timeout
                after = await get_rewrite_provider_pause(db)
                self.assertEqual((after["status"], after["error_code"]), ("blocked", "insufficient_quota"))
                self.assertEqual(after["block_id"], blocked["block_id"])
                self.assertEqual(result["block_id"], blocked["block_id"])
                self.assertEqual(after["state_revision"], blocked["state_revision"])

    async def test_real_completion_cannot_clear_block_created_while_request_in_flight(self):
        for initially_missing in (True, False):
            with self.subTest(initially_missing=initially_missing):
                db = Database()
                if not initially_missing:
                    await record_rewrite_provider_success(db, None)

                async def complete(**_):
                    await record_rewrite_provider_failure(db, classify_rewrite_error(api_error(429, "insufficient_quota")))
                    return "completed-before-pause"

                client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(
                    create=AsyncMock(side_effect=complete))))
                self.assertEqual(await GPTRewriter(db)._create_completion(client), "completed-before-pause")
                after = await get_rewrite_provider_pause(db)
                self.assertEqual((after["status"], after["error_code"]), ("blocked", "insufficient_quota"))

    async def test_old_success_cannot_clear_newer_retry_or_operator_generation(self):
        db = Database()
        await record_rewrite_provider_success(db, None)
        before = await db.rewrite_provider_state.find_one({"_id": PROVIDER_ID})
        retry = await record_rewrite_provider_failure(db, classify_rewrite_error(api_error(503, None)))
        self.assertFalse(await record_rewrite_provider_success(db, before))
        self.assertEqual((await get_rewrite_provider_pause(db))["state_revision"], retry["state_revision"])
        blocked = await record_rewrite_provider_failure(db, classify_rewrite_error(api_error(401, "invalid_api_key")))
        await resume_rewrite_provider(db, expected_block_id=blocked["block_id"], operator_confirmed=True)
        self.assertFalse(await record_rewrite_provider_success(db, before))
        current = await db.rewrite_provider_state.find_one({"_id": PROVIDER_ID})
        self.assertEqual(current["state_revision"], blocked["state_revision"] + 1)


if __name__ == "__main__":
    unittest.main()
