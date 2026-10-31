"""Real headline fixture, captured requests and unchanged publication validators."""
import os
from pathlib import Path
import socket
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline_state import utcnow
from speed_pipeline import GPTRewriter, SpeedPipeline
from test_pipeline_repair import Database
from test_confirmed_french_renewal import TITLE as PULISIC_TITLE, INTRO as PULISIC_SUMMARY


BBC_HEADLINE = "Bellingham agrees new Real deal - Saturday's gossip"
VALID_RENEWAL = ("## Bericht über Bellinghams Vertragsverlängerung\n"
                 "Laut BBC Sport soll Jude Bellingham einer Vertragsverlängerung bei Real Madrid zugestimmt haben.")
REJECTED_LIVE_BODY = ("## Bellingham könnte neuen Vertrag bei Real Madrid erhalten\n\n"
                      "Laut einem Bericht von BBC Sport könnte Bellingham einen neuen Vertrag bei Real Madrid vereinbart haben. "
                      "Details zu den Bedingungen sind jedoch unklar. Weitere Informationen stehen noch aus.")
PULISIC_REJECTED_BODY = (
    "## Vertragsverlängerung bei AC Milan\n\n"
    "Laut Foot Mercato hat der AC Milan die Vertragsverlängerung mit Christian Pulišić "
    "bis zum 30. Juni 2031 offiziell bekannt gegeben. "
    "Der Spieler wird somit seine Zeit beim italienischen Klub fortsetzen.")
PULISIC_NEUTRAL_BODY = PULISIC_REJECTED_BODY.replace("italienischen Klub", "AC Milan")


class TransactionPromptTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = Database()
        self.pipeline = SpeedPipeline(self.db)
        self.pipeline._assign_article_image = AsyncMock()
        env = patch.dict(os.environ, {"OPENAI_API_KEY": "offline-fixture"})
        env.start()
        self.addCleanup(env.stop)
        network = patch.object(socket.socket, "connect", side_effect=AssertionError("No network allowed"))
        network.start()
        self.addCleanup(network.stop)

    async def create_article(self, headline=BBC_HEADLINE, summary="Unrelated roundup: Barcelona are considering another player."):
        await self.pipeline.process_event({"id": "fixture", "status": "pending", "created_at": utcnow(),
            "source_published_at": utcnow(), "headline_raw": headline,
            "summary": summary,
            "source_name": "BBC Sport", "source_url": "https://www.bbc.com/sport/football/articles/fixture"})
        article = await self.db.articles.find_one({})
        self.assertIsNotNone(article)
        self.assertEqual(article["status"], "draft")
        return article

    async def rewrite(self, responses):
        captured = []

        async def complete(**kwargs):
            captured.append(kwargs)
            return types.SimpleNamespace(usage=types.SimpleNamespace(total_tokens=12), choices=[
                types.SimpleNamespace(message=types.SimpleNamespace(content=responses[len(captured) - 1]))])

        client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(
            create=AsyncMock(side_effect=complete))), close=AsyncMock())
        with patch("openai.AsyncOpenAI", return_value=client):
            result = await GPTRewriter(self.db).process_rewrite_queue(1)
        return result, captured

    async def create_pulisic_article(self):
        await self.pipeline.process_event({
            "id": "pulisic-source", "status": "pending", "created_at": utcnow(),
            "source_published_at": utcnow(), "headline_raw": PULISIC_TITLE,
            "body_raw": PULISIC_SUMMARY, "source_name": "Foot Mercato",
            "source_url": "https://www.footmercato.net/a5541281380054695052-ac-milan-christian-pulisic-prolonge-jusquen-2031"})
        article = await self.db.articles.find_one({})
        self.assertEqual((article["status"], article["transfer_status"], article["transfer_type"]),
                         ("draft", "official", "extension"))
        return article

    async def test_actual_pulisic_club_descriptor_requires_neutral_retry(self):
        article = await self.create_pulisic_article()
        result, calls = await self.rewrite([PULISIC_REJECTED_BODY, PULISIC_NEUTRAL_BODY])
        self.assertEqual((result["published"], len(calls)), (1, 2))
        self.assertIn("Unbelegte biografische Angabe", calls[1]["messages"][1]["content"])
        self.assertIn("italienischen", calls[1]["messages"][1]["content"])
        for call in calls:
            for message in call["messages"]:
                self.assertIn("Länder-, Regions- und Nationalitätsbeschreibungen", message["content"])
                self.assertIn("allen Personen und Vereinen", message["content"])
                self.assertIn("Klub oder Verein", message["content"])
            self.assertIn(PULISIC_TITLE, call["messages"][1]["content"])
            self.assertIn(PULISIC_SUMMARY, call["messages"][1]["content"])
            self.assertEqual(call["max_tokens"], 2000)
            self.assertEqual(call["temperature"], 0.1)
        saved = await self.db.articles.find_one({"id": article["id"]})
        self.assertEqual(saved["body"], PULISIC_NEUTRAL_BODY)
        self.assertEqual(saved["source_event_id"], "pulisic-source")
        self.assertEqual(saved["source_headline"], PULISIC_TITLE)
        self.assertEqual(saved["rewrite_validation"], "passed")
        self.assertEqual(saved["rewrite_api_calls"], 2)

    async def test_unchanged_pulisic_country_descriptor_stays_unpublished(self):
        await self.create_pulisic_article()
        result, calls = await self.rewrite([PULISIC_REJECTED_BODY, PULISIC_REJECTED_BODY])
        self.assertEqual((result["published"], result["rejected"], len(calls)), (0, 1, 2))
        saved = await self.db.articles.find_one({})
        self.assertEqual(saved["status"], "draft")
        self.assertIsNone(saved["published_at"])
        self.assertIn("italienischen", saved["rewrite_review_reason"])

    def assert_constraints(self, calls, article, expected_kind):
        constraints = GPTRewriter._source_constraints(article)
        for call in calls:
            user = call["messages"][1]["content"]
            self.assertIn(constraints, user)
            self.assertIn(expected_kind, user)
            self.assertIn('Gerücht / unbestätigter Bericht', user)
            self.assertIn('"soll" oder "könnte"', user)
            self.assertIn("QUELLE: BBC Sport", user)
            self.assertIn(article["source_headline"], user)
            self.assertNotIn("Unrelated roundup", user)
            self.assertIn("Fehlende Angaben weglassen", user)
            self.assertIn("Keine Füllsätze", user)
            self.assertIn('Eine Einigung ("agrees" oder "agreement") belegt keine Unterschrift oder Unterzeichnung', user)
            self.assertIn('Auch "Details sind unbestätigt" ist ohne Quellenbeleg ein Füllsatz', user)
            self.assertIn("ein bis zwei Sätz", user)
            self.assertIn("Ein quellengebundener Kernsatz genügt", user)
            self.assertIn("Kein abschließender Füllsatz", user)
            self.assertIn("Details sind unklar", call["messages"][0]["content"])
            self.assertEqual(call["temperature"], 0.1)

    async def test_real_bbc_renewal_passes_normal_pipeline_with_german_constraints(self):
        article = await self.create_article()
        self.assertEqual((article["transfer_type"], article["transfer_status"], article["evidence_scope"]),
                         ("extension", "rumor", "headline"))
        result, calls = await self.rewrite([VALID_RENEWAL])
        self.assertEqual(result["published"], 1)
        self.assertEqual(len(calls), 1)
        self.assert_constraints(calls, article, "Vertragsverlängerung")
        saved = await self.db.articles.find_one({"id": article["id"]})
        self.assertEqual(saved["body"], VALID_RENEWAL)
        self.assertEqual(saved["transfer_type"], "extension")
        self.assertEqual(saved["rewrite_validation"], "passed")
        self.assertEqual(VALID_RENEWAL.count("."), 1)

    async def test_headline_length_minimum_is_still_enforced(self):
        valid, reason = GPTRewriter(self.db).validate_rewrite(
            "BBC Sport: " + BBC_HEADLINE, "## Bellingham\nLaut BBC Sport soll Bellingham verlängern.",
            evidence=BBC_HEADLINE, evidence_scope="headline")
        self.assertFalse(valid)
        self.assertIn("Zu kurz", reason)

    async def test_live_rejected_wording_is_rejected_then_retry_keeps_full_constraints(self):
        article = await self.create_article()
        result, calls = await self.rewrite([REJECTED_LIVE_BODY, VALID_RENEWAL])
        self.assertEqual((result["published"], len(calls)), (1, 2))
        self.assertIn("unsupported_headline_filler", calls[1]["messages"][1]["content"])
        self.assert_constraints(calls, article, "Vertragsverlängerung")
        for call in calls:
            self.assertIn("kein Vereinswechsel", call["messages"][1]["content"])
        saved = await self.db.articles.find_one({"id": article["id"]})
        self.assertEqual(saved["body"], VALID_RENEWAL)
        self.assertEqual(saved["rewrite_api_calls"], 2)

    async def test_unfixed_live_wording_is_still_reviewed_without_publication(self):
        await self.create_article()
        result, calls = await self.rewrite([REJECTED_LIVE_BODY, REJECTED_LIVE_BODY])
        self.assertEqual((result["published"], result["rejected"], len(calls)), (0, 1, 2))
        saved = await self.db.articles.find_one({})
        self.assertEqual((saved["status"], saved["rewrite_review_reason"]), ("draft", "unsupported_headline_filler"))

    async def test_loan_keeps_loan_and_uncertainty_on_retry(self):
        article = await self.create_article("Endrick linked with Arsenal on loan", summary="")
        self.assertEqual(article["transfer_type"], "loan")
        valid = ("## Endrick im Gespräch für eine Leihe\nLaut BBC Sport könnte Endrick auf Leihbasis zu Arsenal kommen. "
                 "Die Meldung beschreibt eine mögliche Leihe.")
        result, calls = await self.rewrite(["too short", valid])
        self.assertEqual((result["published"], len(calls)), (1, 2))
        self.assert_constraints(calls, article, 'Verwende ausdrücklich "Leihe"')
        for call in calls:
            self.assertIn("kein dauerhafter Kauf", call["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
