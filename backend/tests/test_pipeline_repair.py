"""Offline pipeline regressions. Run: python -m unittest discover -s backend/tests -p test_pipeline_repair.py -v"""
import asyncio
from datetime import timedelta
import os
from pathlib import Path
import socket
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

import mongomock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline_state import utcnow, parse_source_time, story_lease, StoryBusy
from speed_pipeline import SpeedPipeline, GPTRewriter
from story_engine import StoryEngine, AUTHORS
from data_import import RSSFeedScraper, import_rss_events


class Cursor:
    def __init__(self, cursor): self.cursor = cursor
    def sort(self, *args): self.cursor.sort(*args); return self
    def limit(self, count): self.cursor.limit(count); return self
    async def to_list(self, length): return list(self.cursor)[:length]


class Collection:
    def __init__(self, collection): self.raw = collection
    def find(self, *args, **kwargs): return Cursor(self.raw.find(*args, **kwargs))
    def __getattr__(self, name):
        async def operation(*args, **kwargs):
            # Yield like a real driver, then perform the Mongo operation atomically.
            await asyncio.sleep(0)
            return getattr(self.raw, name)(*args, **kwargs)
        return operation


class Database:
    def __init__(self): self.raw = mongomock.MongoClient(tz_aware=True).pipeline_test
    def __getattr__(self, name): return Collection(self.raw[name])


class Generator:
    def extract_entities(self, title, body=""):
        return {"player": "Florian Wirtz", "club": "FC Liverpool", "from_club": "Former Club"}
    def generate_instant_article(self, event):
        return {"title": "Fixture", "body": event.get("title", "Fixture"),
                "source_url": event.get("source_url"), "source_name": event.get("source_name"),
                "player_name": "Florian Wirtz", "club_name": "FC Liverpool", "needs_gpt_rewrite": True}


class PipelineRepairTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = Database()
        self.pipeline = SpeedPipeline(self.db)
        self.pipeline.instant_generator = Generator()
        self.pipeline._assign_article_image = AsyncMock()
        self.env = patch.dict(os.environ, {"OPENAI_API_KEY": "offline-fixture-not-a-real-key"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.network = patch.object(socket.socket, "connect", side_effect=AssertionError("External networking is prohibited"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def event(self, number=0, **overrides):
        return {"id": f"event-{number}", "status": "pending", "created_at": utcnow() + timedelta(microseconds=number),
                "headline_raw": "Florian Wirtz linked with FC Liverpool", "body_raw": "The source reports transfer interest.",
                "source_name": "Source A", "source_url": f"https://source.invalid/{number}",
                "source_published_at": utcnow(), **overrides}

    async def test_twenty_one_events_complete_without_starvation(self):
        await self.db.events.insert_many([self.event(i) for i in range(21)])
        first = await self.pipeline.process_pending_events(20)
        second = await self.pipeline.process_pending_events(20)
        self.assertEqual((first["processed"], second["processed"]), (20, 1))
        self.assertEqual(await self.db.events.count_documents({"status": "pending"}), 0)
        self.assertEqual(await self.db.events.count_documents({"status": "processed"}), 21)
        self.assertEqual(await self.db.articles.count_documents({}), 1)

    async def test_official_title_loan_fee_and_summary_survive(self):
        result = await self.pipeline.process_event(self.event(headline_raw="Official: Florian Wirtz joins FC Liverpool on loan for 20 million euro"))
        story = await self.db.transfer_stories.find_one({})
        self.assertEqual(story["current_stage"], "official")
        self.assertEqual(story["transfer_type"], "loan")
        self.assertEqual(story["transfer_fee"], "20 Mio. €")
        self.assertTrue(story["sources"][0]["raw_title"].startswith("Official:"))
        self.assertIn("source reports", story["sources"][0]["raw_summary"])
        self.assertEqual(result["action"], "created")

    async def test_article_uses_entities_resolved_from_summary(self):
        self.pipeline.instant_generator.generate_instant_article = lambda event: {
            "title": "Template", "body": "Template", "player_name": "Unbekannter Spieler",
            "club_name": "Unbekannter Verein", "needs_gpt_rewrite": True}
        await self.pipeline.process_event(self.event(headline_raw="Official transfer announced", body_raw="Florian Wirtz joins FC Liverpool"))
        article = await self.db.articles.find_one({})
        self.assertEqual(article["player_name"], "Florian Wirtz")
        self.assertEqual(article["club_name"], "FC Liverpool")
        self.assertIn("Florian Wirtz joins FC Liverpool", article["body"])

    async def test_same_source_new_url_and_facts_upgrade_existing_article(self):
        first = await self.pipeline.process_event(self.event())
        second = await self.pipeline.process_event(self.event(1, headline_raw="Official: Florian Wirtz has signed for FC Liverpool"))
        self.assertEqual(first["article_id"], second["article_id"])
        story = await self.db.transfer_stories.find_one({})
        article = await self.db.articles.find_one({})
        self.assertEqual(story["current_stage"], "official")
        self.assertEqual(len(story["sources"]), 1)
        self.assertEqual(article["status"], "published")

    async def test_exact_duplicate_is_completed_as_skipped(self):
        event = self.event()
        await self.pipeline.process_event(event)
        await self.db.events.insert_one(event)
        result = await self.pipeline.process_pending_events()
        saved = await self.db.events.find_one({"id": event["id"]})
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(saved["status"], "processed")

    async def test_draft_promotion_and_score_sync(self):
        for i, source in enumerate(["Source A", "Source B", "Source C"]):
            await self.pipeline.process_event(self.event(i, source_name=source))
        article = await self.db.articles.find_one({})
        self.assertEqual(article["status"], "published")
        self.assertEqual(article["confidence_score"], 45)
        self.assertIsNotNone(article["published_at"])

    async def test_old_missing_future_and_unknown_are_reviewed_before_story_creation(self):
        for value, reason in [(utcnow() - timedelta(days=10), "stale_source"), (None, "missing_source_date"),
                              (utcnow() + timedelta(days=1), "future_source_date")]:
            outcome = await self.pipeline.process_event(self.event(source_published_at=value))
            self.assertEqual((outcome["action"], outcome["reason"]), ("review", reason))
        await self.db.events.insert_one(self.event(headline_raw="Unknown footballer linked with FC Liverpool"))
        result = await self.pipeline.process_pending_events()
        self.assertEqual(result["review"], 1)
        self.assertEqual(await self.db.transfer_stories.count_documents({}), 0)
        self.assertEqual(await self.db.articles.count_documents({}), 0)

    async def test_failed_event_has_backoff_and_does_not_block_next(self):
        await self.db.events.insert_many([self.event(i) for i in range(4)])
        actual = self.pipeline.process_event
        async def process(event):
            if event["id"] == "event-0": raise ValueError("synthetic failure")
            return await actual(event)
        self.pipeline.process_event = process
        result = await self.pipeline.process_pending_events(4)
        bad = await self.db.events.find_one({"id": "event-0"})
        self.assertEqual(bad["status"], "retry")
        self.assertGreater(bad["next_attempt_at"], utcnow())
        self.assertEqual(result["processed"], 3)
        self.assertEqual(bad["error"], "ValueError")

    async def test_fifth_event_failure_is_terminal(self):
        await self.db.events.insert_one(self.event(processing_attempts=4))
        self.pipeline.process_event = AsyncMock(side_effect=RuntimeError("fixture"))
        await self.pipeline.process_pending_events()
        self.assertEqual((await self.db.events.find_one({}))["status"], "error")

    async def test_expired_lease_recovered_live_lease_untouched(self):
        await self.db.events.insert_many([
            self.event(0, status="processing", lease_until=utcnow()-timedelta(minutes=1)),
            self.event(1, status="processing", lease_until=utcnow()+timedelta(minutes=5)),
        ])
        result = await self.pipeline.process_pending_events()
        self.assertEqual(result["processed"], 1)
        self.assertEqual((await self.db.events.find_one({"id": "event-1"}))["status"], "processing")

    async def test_parallel_workers_claim_event_only_once(self):
        await self.db.events.insert_one(self.event())
        counts = await asyncio.gather(self.pipeline.process_pending_events(), self.pipeline.process_pending_events())
        self.assertEqual(sum(result["processed"] for result in counts), 1)
        self.assertEqual(await self.db.articles.count_documents({}), 1)

    async def test_story_lease_prevents_concurrent_writers(self):
        async with story_lease(self.db, "same-story"):
            with self.assertRaises(StoryBusy):
                async with story_lease(self.db, "same-story"):
                    self.fail("second writer obtained active lease")
        async with story_lease(self.db, "same-story"):
            pass

    async def test_story_does_not_expire_and_legacy_url_is_preserved(self):
        first = await self.pipeline.process_event(self.event())
        story = await self.db.transfer_stories.find_one({})
        await self.db.transfer_stories.update_one({"_id": story["_id"]}, {"$set": {"last_updated_at": "2000-01-01T00:00:00+00:00"}})
        second = await self.pipeline.process_event(self.event(1, source_name="Source B"))
        self.assertEqual(first["article_id"], second["article_id"])
        self.assertEqual(await self.db.transfer_stories.count_documents({}), 1)
        self.assertEqual((await self.db.articles.find_one({}))["slug"], story["slug"])

    async def test_transfer_types_have_distinct_slugs(self):
        engine = StoryEngine(self.db)
        self.assertNotEqual(engine.generate_story_slug("player", "club", "loan"), engine.generate_story_slug("player", "club", "permanent"))
        self.assertEqual(engine._detect_transfer_type("ablösefrei"), "free")
        self.assertEqual(engine._detect_stage("The move is not yet official"), "rumor")

    async def test_missing_article_is_recovered_idempotently(self):
        first = await self.pipeline.process_event(self.event())
        await self.db.articles.delete_many({})
        recovered = await self.pipeline.process_event(self.event())
        self.assertEqual(first["article_id"], recovered["article_id"])
        self.assertEqual(await self.db.transfer_stories.count_documents({}), 1)
        self.assertEqual(await self.db.articles.count_documents({}), 1)

    async def test_retry_recovers_article_after_story_was_saved(self):
        await self.pipeline.process_event(self.event())
        update_event = self.event(1, headline_raw="Official: Florian Wirtz has signed for FC Liverpool")
        actual = self.pipeline._update_article_from_story
        self.pipeline._update_article_from_story = AsyncMock(side_effect=RuntimeError("interrupted write"))
        with self.assertRaises(RuntimeError):
            await self.pipeline.process_event(update_event)
        self.assertEqual((await self.db.transfer_stories.find_one({}))["current_stage"], "official")
        self.assertEqual((await self.db.articles.find_one({}))["transfer_status"], "rumor")
        self.pipeline._update_article_from_story = actual
        await self.pipeline.process_event(update_event)
        self.assertEqual((await self.db.articles.find_one({}))["transfer_status"], "official")

    async def test_updates_persist_rewrite_work_and_invalidate_running_rewrite(self):
        await self.pipeline.process_event(self.event())
        await self.db.articles.update_one({}, {"$set": {"needs_gpt_rewrite": False, "rewrite_token": "old", "rewrite_attempts": 4}})
        await self.pipeline.process_event(self.event(1, source_name="Source B"))
        saved = await self.db.articles.find_one({})
        self.assertTrue(saved["needs_gpt_rewrite"])
        self.assertEqual(saved["rewrite_attempts"], 0)
        self.assertEqual(saved["content_revision"], 2)
        self.assertNotIn("rewrite_token", saved)

    async def test_failed_rewrite_backoff_reaches_fourth_article(self):
        await self.db.articles.insert_many([{"id": f"a{i}", "needs_gpt_rewrite": True, "published_at": str(i)} for i in range(4)])
        rewriter = GPTRewriter(self.db)
        seen = []
        async def fail(article_id): seen.append(article_id); return False
        rewriter.rewrite_article = fail
        await rewriter.process_rewrite_queue(3)
        await rewriter.process_rewrite_queue(3)
        self.assertEqual(seen, ["a0", "a1", "a2", "a3"])
        self.assertEqual(await self.db.articles.count_documents({"rewrite_status": "retry"}), 4)

    async def test_rewrite_failure_limit_and_success(self):
        await self.db.articles.insert_many([
            {"id": "bad", "needs_gpt_rewrite": True, "rewrite_attempts": 4},
            {"id": "good", "needs_gpt_rewrite": True},
        ])
        rewriter = GPTRewriter(self.db)
        async def rewrite(article_id): return article_id == "good"
        rewriter.rewrite_article = rewrite
        result = await rewriter.process_rewrite_queue()
        self.assertEqual(result["rewritten"], 1)
        self.assertEqual((await self.db.articles.find_one({"id": "bad"}))["rewrite_status"], "failed")
        self.assertFalse((await self.db.articles.find_one({"id": "bad"}))["needs_gpt_rewrite"])

    async def test_emergent_key_does_not_enable_openai(self):
        with patch.dict(os.environ, {"EMERGENT_LLM_KEY": "not-an-openai-key"}, clear=True):
            rewriter = GPTRewriter(self.db)
            rewriter.rewrite_article = AsyncMock()
            result = await rewriter.process_rewrite_queue()
            self.assertEqual(result["blocked"], "missing_openai_key")
            rewriter.rewrite_article.assert_not_awaited()

    async def test_real_rewrite_path_preserves_concurrent_source_update(self):
        await self.pipeline.process_event(self.event())
        article = await self.db.articles.find_one({})
        text = "## Transfer\n" + ("Der Spieler und der Verein stehen nach Angaben der Quelle weiter im Mittelpunkt des Berichts. " * 12) + "\n## Quelle\nWeitere Angaben enthält die Meldung nicht."
        context = types.SimpleNamespace(found=True, sources=["Fixture"], market_value=None, contract_until=None,
                                        age=None, nationality=None, position=None, full_name=None, current_club=None,
                                        to_context_text=lambda: "")
        service = types.SimpleNamespace(get_full_player_context=AsyncMock(return_value=context))
        module = types.ModuleType("context_scraper")
        module.get_context_service = lambda db: service
        async def complete(**kwargs):
            self.assertIn("QUELLENZUSAMMENFASSUNG", kwargs["messages"][1]["content"])
            await self.db.articles.update_one({"id": article["id"]}, {"$set": {"body": "New source update"}, "$inc": {"content_revision": 1}})
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=text))])
        client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=AsyncMock(side_effect=complete))), close=AsyncMock())
        with patch.dict(sys.modules, {"context_scraper": module}), patch("openai.AsyncOpenAI", return_value=client):
            rewritten = await GPTRewriter(self.db).rewrite_article(article["id"])
        self.assertFalse(rewritten)
        self.assertEqual((await self.db.articles.find_one({"id": article["id"]}))["body"], "New source update")
        client.close.assert_awaited_once()

    async def test_unsupported_number_rejected_and_sterling_not_relabelled(self):
        original = "## Transfer\n" + ("Die Quelle berichtet über den Spieler und den Verein ohne weitere bestätigte Angaben. " * 10) + "\n## Quelle\nWeitere Details fehlen."
        rewritten = original + " Die Ablöse beträgt 99 Millionen Euro."
        valid, reason = GPTRewriter(self.db).validate_rewrite(original, rewritten)
        self.assertFalse(valid)
        self.assertIn("Statistiken", reason)
        self.assertEqual(StoryEngine(self.db)._extract_transfer_fee("20 million pounds"), "20 Mio. £")

    async def test_rss_identity_full_title_versions_and_tracking_urls(self):
        rss = RSSFeedScraper()
        prefix = "Transfer " + "x" * 100
        self.assertNotEqual(rss._generate_dedupe_key(prefix+"a", "s"), rss._generate_dedupe_key(prefix+"b", "s"))
        self.assertEqual(rss._generate_dedupe_key("Title", "s", "https://x.invalid/a?utm_source=a"),
                         rss._generate_dedupe_key("Title", "s", "https://x.invalid/a?utm_source=b"))
        self.assertNotEqual(rss._generate_dedupe_key("Title", "s", "https://x.invalid/a", "old"),
                            rss._generate_dedupe_key("Title", "s", "https://x.invalid/a", "new"))
        self.assertTrue(rss._is_transfer_related("Player signs for Club in transfer after injury update", "", "en"))

    async def test_rss_import_retains_source_contract_and_is_idempotent(self):
        now = utcnow()
        fixture = {"headline_raw": "Player transfer to Club", "summary": "Loan for 20 million euro", "source_key": "fixture",
                   "source_name": "Fixture", "source_url": "https://source.invalid/article", "dedupe_key": "fixture-version",
                   "source_published_at": now, "language": "en", "category": "tier_2"}
        feeds = {"fixture": {"name": "Fixture", "url": "https://source.invalid/feed", "category": "tier_2"}}
        with patch.object(RSSFeedScraper, "FEEDS", feeds), patch.object(RSSFeedScraper, "fetch_all_feeds", AsyncMock(return_value=[fixture])):
            first = await import_rss_events(self.db)
            second = await import_rss_events(self.db)
        saved = await self.db.events.find_one({})
        self.assertEqual(first["new_events"], 1)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(saved["summary"], fixture["summary"])
        self.assertEqual(saved["body_raw"], fixture["summary"])
        self.assertEqual(saved["title"], fixture["headline_raw"])
        self.assertLess(abs((saved["source_published_at"] - now).total_seconds()), 0.001)

    async def test_rss_stream_is_consumed_before_response_closes(self):
        rss = RSSFeedScraper()
        now = utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        xml = f'<rss version="2.0"><channel><title>Fixture</title><item><title>Player signs transfer</title><description>&lt;p&gt;Loan details&lt;/p&gt;</description><link>https://source.invalid/item</link><pubDate>{now}</pubDate></item></channel></rss>'.encode()
        state = {"closed": True, "chunks_read": 0}
        async def chunks(size):
            for start in range(0, len(xml), 40):
                # aiohttp releases/closes the response on __aexit__; unread streams
                # cannot be consumed afterward. Yield between chunks like network I/O.
                await asyncio.sleep(0)
                if state["closed"]:
                    from aiohttp import ClientConnectionError
                    raise ClientConnectionError("Connection closed")
                state["chunks_read"] += 1
                yield xml[start:start + 40]
        response = types.SimpleNamespace(status=200, content=types.SimpleNamespace(iter_chunked=chunks))
        class Context:
            async def __aenter__(self):
                state["closed"] = False
                return response
            async def __aexit__(self, *args):
                state["closed"] = True
        class Session:
            def __init__(self, **kwargs):
                self.timeout = kwargs["timeout"]
                assert self.timeout.total == 20
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            def get(self, *args, **kwargs): return Context()
        with patch("data_import.aiohttp.ClientSession", Session):
            events = await rss.fetch_feed(next(iter(rss.FEEDS)))
        self.assertEqual(len(events), 1)
        self.assertGreater(state["chunks_read"], 1)
        self.assertTrue(state["closed"])
        self.assertEqual(rss.feed_errors, {})
        self.assertEqual(events[0]["summary"], "Loan details")
        self.assertIsNotNone(events[0]["source_published_at"])

    async def test_only_real_editorial_byline(self):
        self.assertEqual([author["name"] for author in AUTHORS], ["Redaktion"])
        await self.pipeline.process_event(self.event())
        self.assertEqual((await self.db.articles.find_one({}))["author_name"], "Redaktion")


if __name__ == "__main__":
    unittest.main()
