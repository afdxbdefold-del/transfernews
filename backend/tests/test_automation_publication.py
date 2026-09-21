"""Offline end-to-end regression of scheduled selection, rewriting and publication."""
import os
from pathlib import Path
import socket
import sys
import types
import unittest
from datetime import timedelta
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_pipeline_repair import Database
from pipeline_state import utcnow
from publication_policy import PIPELINE_VERSION, editorial_eligibility
from speed_pipeline import SpeedPipeline, GPTRewriter


TEXT = ("## Endrick im Gespräch\nBBC Sport berichtet, dass Arsenal im Januar einen Vorstoß für Endrick erwägen könnte. "
        "Die Gerüchtemeldung beschreibt eine mögliche Entwicklung und keinen bestätigten Wechsel.")


class AutomationPublicationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = Database()
        self.pipeline = SpeedPipeline(self.db)
        self.pipeline._assign_article_image = AsyncMock()
        self.network = patch.object(socket.socket, "connect", side_effect=AssertionError("No external network"))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.env = patch.dict(os.environ, {"OPENAI_API_KEY": "offline-test"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def event(self, **changes):
        return {"id": "fresh", "status": "pending", "created_at": utcnow(),
                "source_published_at": utcnow(), "headline_raw": "Arsenal may move for Endrick in January",
                "summary": "", "source_name": "BBC Sport",
                "source_url": "https://www.bbc.com/sport/football/articles/fixture", **changes}

    def client(self, text=TEXT, callback=None):
        async def complete(**kwargs):
            if callback:
                await callback(kwargs)
            return types.SimpleNamespace(id="offline-response", usage=types.SimpleNamespace(total_tokens=123),
                choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=text))])
        return types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(
            create=AsyncMock(side_effect=complete))), close=AsyncMock())

    async def test_single_source_report_publishes_only_after_validated_rewrite(self):
        await self.db.events.insert_one(self.event())
        result = await self.pipeline.process_pending_events(1)
        self.assertEqual(result["created_draft"], 1)
        article = await self.db.articles.find_one({})
        self.assertEqual((article["status"], article["confidence_score"]), ("draft", 41))
        self.assertTrue(article["auto_publish_eligible"])
        self.assertIsNone(article["published_at"])
        with patch("openai.AsyncOpenAI", return_value=self.client()):
            rewritten = await GPTRewriter(self.db).process_rewrite_queue(1)
        article = await self.db.articles.find_one({})
        self.assertEqual(rewritten["rewritten"], 1)
        self.assertEqual((article["status"], article["confidence_score"], article["rewrite_status"]),
                         ("published", 41, "complete"))
        self.assertEqual(article["rewrite_completed_revision"], article["content_revision"])
        self.assertEqual(article["body"], TEXT)
        self.assertEqual(article["rewrite_tokens"], 123)
        self.assertFalse(article["has_researched_context"])

    async def test_publisher_name_cannot_spoof_domain_even_for_official_score(self):
        await self.pipeline.process_event(self.event(
            headline_raw="Official: Endrick joins Arsenal", source_url="https://bbc.com.attacker.invalid/claim"))
        article = await self.db.articles.find_one({})
        self.assertEqual(article["status"], "draft")
        self.assertFalse(article["auto_publish_eligible"])
        self.assertFalse(article["needs_gpt_rewrite"])

    async def test_spanish_renewal_can_publish_a_grounded_german_translation(self):
        await self.pipeline.process_event(self.event(
            headline_raw="La cláusula que tendrá Bernal en su nuevo contrato",
            summary=("El futuro de Marc Bernal en el Barça tiene fecha. El centrocampista está a punto de ampliar su contrato hasta 2031. "
                     "Ampliará su vinculación contractual un par de temporadas más. El propio director deportivo Deco anunció el inmediato acuerdo en la última asamblea."),
            source_name="Mundo Deportivo",
            source_url="https://www.mundodeportivo.com/futbol/fc-barcelona/fixture.html"))
        draft = await self.db.articles.find_one({})
        self.assertEqual((draft["status"], draft["transfer_type"]), ("draft", "extension"))
        rewrite = ("## Marc Bernal steht vor Vertragsverlängerung beim FC Barcelona\n\n"
                   "Laut Mundo Deportivo steht Marc Bernal kurz davor, seinen Vertrag beim FC Barcelona bis 2031 zu verlängern. "
                   "Der Mittelfeldspieler wird demnach seine vertragliche Bindung um zwei weitere Jahre ausdehnen. "
                   "Der Sportdirektor Deco bestätigte das bevorstehende Einvernehmen während der letzten Versammlung.")
        with patch("openai.AsyncOpenAI", return_value=self.client(rewrite)):
            result = await GPTRewriter(self.db).process_rewrite_queue(1)
        article = await self.db.articles.find_one({})
        self.assertEqual(result["published"], 1)
        self.assertEqual(article["body"], rewrite)
        self.assertEqual(article["transfer_status"], "rumor")
        self.assertEqual(article["confidence_score"], 41)

    async def test_review_reconsidered_once_per_version_but_old_backlog_untouched(self):
        await self.db.events.insert_many([
            self.event(status="review", review_reason="unresolved_entities"),
            self.event(id="old", status="review", review_reason="unresolved_entities",
                       source_published_at=utcnow() - timedelta(days=10)),
            self.event(id="ambiguous", status="review", review_reason="ambiguous_players",
                       headline_raw="Arsenal interested in Endrick and Florian Wirtz"),
        ])
        first = await self.pipeline.process_pending_events(10)
        second = await self.pipeline.process_pending_events(10)
        self.assertEqual((first["processed"], second["processed"]), (2, 0))
        self.assertEqual((await self.db.events.find_one({"id": "fresh"}))["pipeline_version"], PIPELINE_VERSION)
        self.assertNotIn("pipeline_version", await self.db.events.find_one({"id": "old"}))
        self.assertEqual((await self.db.events.find_one({"id": "ambiguous"}))["status"], "review")

    async def test_new_database_player_is_used_by_pipeline(self):
        await self.db.players.insert_one({"name": "Lennard Meyer", "aliases": ["Lenny Meyer"],
                                          "current_club": "Bayern"})
        await self.pipeline.process_event(self.event(headline_raw="Lenny Meyer linked with Arsenal"))
        article = await self.db.articles.find_one({})
        self.assertEqual(article["player_name"], "Lennard Meyer")
        self.assertEqual(article["club_name"], "FC Arsenal")
        self.assertIsNone(article["from_club"])

    async def test_invalid_rewrite_never_publishes(self):
        await self.pipeline.process_event(self.event())
        invalid = ("## Endrick wechselt\nBBC Sport hat den Transfer von Endrick zu Arsenal offiziell bestätigt. "
                   "Der Vertrag wurde unterschrieben und der Wechsel ist damit endgültig abgeschlossen.")
        with patch("openai.AsyncOpenAI", return_value=self.client(invalid)):
            result = await GPTRewriter(self.db).process_rewrite_queue(1)
        article = await self.db.articles.find_one({})
        self.assertEqual(result["rejected"], 1)
        self.assertEqual(article["status"], "draft")
        self.assertIsNone(article["published_at"])
        self.assertEqual(article["rewrite_rejected_body"], invalid)

    async def test_source_becoming_stale_during_api_call_cannot_publish(self):
        await self.pipeline.process_event(self.event())
        later = utcnow() + timedelta(days=3)
        with patch("openai.AsyncOpenAI", return_value=self.client()), patch("pipeline_state.utcnow", return_value=later):
            self.assertFalse(await GPTRewriter(self.db).rewrite_article((await self.db.articles.find_one({}))["id"]))
        self.assertEqual((await self.db.articles.find_one({}))["status"], "draft")

    async def test_published_body_stays_until_new_revision_validates_and_old_response_loses(self):
        await self.pipeline.process_event(self.event())
        article = await self.db.articles.find_one({})
        with patch("openai.AsyncOpenAI", return_value=self.client()):
            await GPTRewriter(self.db).process_rewrite_queue(1)
        await self.pipeline.process_event(self.event(id="update", headline_raw="Arsenal interested in Endrick",
                                                    source_url="https://www.bbc.com/sport/football/articles/update"))
        staged = await self.db.articles.find_one({})
        self.assertEqual(staged["body"], TEXT)
        self.assertIn("pending_publication", staged)
        self.assertNotIn("rewrite_validation", staged)
        async def new_revision(_):
            await self.pipeline.process_event(self.event(id="newer", headline_raw="Arsenal may move for Endrick in February",
                source_url="https://www.bbc.com/sport/football/articles/newer"))
        with patch("openai.AsyncOpenAI", return_value=self.client(callback=new_revision)):
            self.assertFalse(await GPTRewriter(self.db).rewrite_article(article["id"]))
        saved = await self.db.articles.find_one({})
        self.assertEqual(saved["body"], TEXT)
        self.assertGreater(saved["content_revision"], staged["content_revision"])

    async def test_editorial_hold_during_openai_blocks_draft_and_published_writes(self):
        for status in ("draft", "published"):
            for field in ("duplicate_of", "review_reason"):
                with self.subTest(status=status, field=field):
                    db = Database()
                    pipeline = SpeedPipeline(db)
                    pipeline._assign_article_image = AsyncMock()
                    await pipeline.process_event(self.event())
                    if status == "published":
                        with patch("openai.AsyncOpenAI", return_value=self.client()):
                            await GPTRewriter(db).process_rewrite_queue(1)
                        await pipeline.process_event(self.event(id="update", source_url="https://bbc.com/sport/update"))
                    before = await db.articles.find_one({})
                    self.assertEqual(before["status"], status)

                    async def apply_hold(_):
                        await db.articles.update_one({"id": before["id"]}, {"$set": {field: "editorial-hold"}})

                    with patch("openai.AsyncOpenAI", return_value=self.client(callback=apply_hold)):
                        result = await GPTRewriter(db).process_rewrite_queue(1)
                    saved = await db.articles.find_one({})
                    self.assertEqual((result["rewritten"], result["published"]), (0, 0))
                    self.assertEqual(saved[field], "editorial-hold")
                    self.assertEqual(saved["status"], status)
                    self.assertEqual(saved["body"], before["body"])
                    self.assertEqual(saved["content_revision"], before["content_revision"])
                    self.assertEqual(saved.get("published_at"), before.get("published_at"))
                    self.assertNotEqual(saved["rewrite_status"], "complete")


if __name__ == "__main__":
    unittest.main()
