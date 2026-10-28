"""Scheduler-to-publication coverage for exact claim spans, with no network."""
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
from speed_pipeline import SpeedPipeline, GPTRewriter


class ClaimScopePipelineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = Database()
        self.pipeline = SpeedPipeline(self.db)
        self.pipeline._assign_article_image = AsyncMock()
        self.claim = "Morris Schröter unterschreibt beim FSV Zwickau bis 2028."
        self.event = {"id": "claim-test", "status": "pending", "created_at": utcnow(),
                      "source_published_at": utcnow(), "headline_raw": "Transfer-Coup",
                      "body_raw": self.claim + " Trainer Mikel Arteta sprach über Arsenal.",
                      "source_name": "BILD", "source_url": "https://www.bild.de/sport/fussball/fixture"}
        self.evidence = {"player": "Morris Schröter", "club": "FSV Zwickau", "from_club": None,
                         "confidence": 1.0, "reason": None, "transfer_type": "permanent",
                         "verified_stage": "official", "evidence_scope": "claim",
                         "evidence_headline": self.claim, "evidence_summary": "",
                         "evidence_spans": [{"field": "summary", "start": 0,
                                             "end": len(self.claim), "text": self.claim}]}
        for context in (patch.object(socket.socket, "connect", side_effect=AssertionError("Network disabled")),
                        patch.dict(os.environ, {"OPENAI_API_KEY": "offline-test"})):
            context.start()
            self.addCleanup(context.stop)

    async def test_exact_scoped_source_survives_scheduler_and_checked_rewrite(self):
        await self.db.events.insert_one(self.event)
        with patch("speed_pipeline.assess_transfer_evidence", return_value=self.evidence):
            processed = await self.pipeline.process_pending_events(1)
        self.assertEqual(processed["created_draft"], 1)
        draft = await self.db.articles.find_one({})
        self.assertEqual((draft["status"], draft["evidence_scope"], draft["transfer_status"]),
                         ("draft", "claim", "official"))
        self.assertEqual(draft["source_headline"], self.claim)
        self.assertEqual(draft["original_source_headline"], "Transfer-Coup")
        self.assertEqual(draft["source_summary"], "")
        self.assertEqual(draft["title"], "Bericht: Morris Schröter wechselt zu FSV Zwickau")
        self.assertIn("Mikel Arteta", (await self.db.events.find_one({"id": "claim-test"}))["body_raw"])
        rewrite = ("## Morris Schröter unterschreibt beim FSV Zwickau\n\n"
                   "Laut BILD hat Morris Schröter beim FSV Zwickau einen Vertrag bis 2028 unterschrieben.")
        async def complete(**kwargs):
            prompt = str(kwargs["messages"])
            self.assertIn(self.claim, prompt)
            self.assertNotIn("Arteta", prompt)
            self.assertNotIn("Arsenal", prompt)
            return types.SimpleNamespace(usage=types.SimpleNamespace(total_tokens=100),
                choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=rewrite))])
        client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(
            create=AsyncMock(side_effect=complete))), close=AsyncMock())
        with patch("openai.AsyncOpenAI", return_value=client):
            result = await GPTRewriter(self.db).process_rewrite_queue(1)
        published = await self.db.articles.find_one({})
        self.assertEqual(result["published"], 1)
        self.assertEqual(published["body"], rewrite)
        self.assertEqual(published["rewrite_status"], "complete")
        self.assertFalse(published["has_researched_context"])

    async def test_forged_claim_cannot_create_an_article(self):
        evidence = {**self.evidence, "evidence_headline": self.claim.replace("2028", "2030")}
        with patch("speed_pipeline.assess_transfer_evidence", return_value=evidence):
            with self.assertRaisesRegex(ValueError, "unverifiable_source_claim_text"):
                await self.pipeline.process_event(self.event)
        self.assertEqual(await self.db.articles.count_documents({}), 0)

    async def test_actual_return_claim_does_not_invent_a_signature_in_the_title(self):
        headline = "Neuzugang: Nico Neumann kehrt nach SC Hafenstadt zurück"
        event = {**self.event, "id": "return-claim-test", "headline_raw": headline,
                 "body_raw": "He played for Arsenal."}
        await self.db.events.insert_one(event)
        result = await self.pipeline.process_pending_events(1)
        self.assertEqual(result["created_draft"], 1)
        draft = await self.db.articles.find_one({})
        self.assertEqual((draft["evidence_scope"], draft["transfer_status"]), ("claim", "done"))
        self.assertEqual(draft["title"], "Bericht über Wechsel von Nico Neumann zu SC Hafenstadt")
        self.assertNotIn("Unterschrift", draft["title"])
        self.assertEqual(draft["source_headline"], headline)
        self.assertEqual(draft["source_summary"], "")
        self.assertEqual(draft["evidence_spans"], [
            {"field": "headline", "start": 0, "end": len(headline), "text": headline}])
        self.assertEqual((await self.db.events.find_one({"id": "return-claim-test"}))["body_raw"],
                         "He played for Arsenal.")

    async def test_policy_reconsideration_leaves_sources_older_than_one_day_untouched(self):
        await self.db.events.insert_one({**self.event, "status": "review",
            "pipeline_version": "previous-policy", "review_reason": "unresolved_entities",
            "source_published_at": utcnow() - timedelta(hours=25)})
        result = await self.pipeline.process_pending_events(10)
        self.assertEqual(result["processed"], 0)
        self.assertEqual((await self.db.events.find_one({}))["pipeline_version"], "previous-policy")


if __name__ == "__main__":
    unittest.main()
