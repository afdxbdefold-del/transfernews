"""Offline regressions for evidence-based direction and pre-write review decisions."""
from datetime import datetime, timezone
from pathlib import Path
import os
import socket
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline_state import parse_source_time, utcnow
from speed_pipeline import SpeedPipeline, GPTRewriter
from transfer_evidence import assess_transfer_evidence
from test_pipeline_repair import Database


# Verified RSS text, 20 September 2026. The description is a three-story roundup.
BBC_TITLE = "Arsenal may move for Endrick in January - Sunday's gossip"
BBC_SUMMARY = ("Barcelona may launch a huge offer for Haaland, Arsenal are interested in struggling Endrick, "
               "and Liverpool insist on keeping Wirtz")


class EvidenceTests(unittest.TestCase):
    def test_standalone_bbc_headline_isolated_without_relaxing_ambiguity(self):
        result = assess_transfer_evidence(BBC_TITLE, BBC_SUMMARY)
        self.assertEqual((result["player"], result["club"], result["from_club"], result["evidence_scope"]),
                         ("Endrick", "FC Arsenal", None, "headline"))
        self.assertEqual(assess_transfer_evidence("Arsenal may move for Endrick and Wirtz", BBC_SUMMARY)["reason"], "ambiguous_players")
        self.assertEqual(assess_transfer_evidence("Arsenal and Liverpool may move for Endrick", BBC_SUMMARY)["reason"], "ambiguous_players")
        self.assertIsNotNone(assess_transfer_evidence("Arsenal may move for Endrick and an unnamed player", BBC_SUMMARY)["reason"])
        self.assertEqual(assess_transfer_evidence(BBC_TITLE, BBC_SUMMARY + ". This is for a charity match.")["reason"], "non_transfer_topic")
        self.assertEqual(assess_transfer_evidence(BBC_TITLE, BBC_SUMMARY + ". Arsenal will not move for Endrick.")["reason"], "negated_transfer")
        self.assertEqual(assess_transfer_evidence(BBC_TITLE.replace("may move", "may not move"), BBC_SUMMARY)["reason"], "negated_transfer")
        self.assertIsNotNone(assess_transfer_evidence("Arsenal monitor Brazilian sensation ahead of January transfer window",
            "Arsenal could secure Real Madrid forward Endrick.")["reason"])

    def test_headline_rewrite_is_short_but_still_rejects_invented_numbers(self):
        rewriter = GPTRewriter(None)
        text = ("## Endrick im Gespräch\nBBC Sport berichtet, dass Arsenal im Januar einen Vorstoß für Endrick erwägen könnte. "
                "Die Überschrift der Gerüchterundschau beschreibt damit eine mögliche Entwicklung und keinen bestätigten Wechsel.")
        self.assertTrue(rewriter.validate_rewrite(BBC_TITLE, text, evidence_scope="headline")[0])
        valid, reason = rewriter.validate_rewrite(BBC_TITLE, text + " Die Ablöse beträgt 999 Millionen Euro.", evidence_scope="headline")
        self.assertFalse(valid)
        self.assertIn("Statistiken", reason)
        self.assertFalse(rewriter.validate_rewrite(BBC_TITLE, text * 4, evidence_scope="headline")[0])

    def test_headline_rewrite_rejects_actual_live_biographical_addition(self):
        rewriter = GPTRewriter(None)
        safe = ("## Endrick im Gespräch\nLaut BBC Sport könnte der FC Arsenal im Januar einen Transfer für "
                "den Spieler Endrick ins Auge fassen. Die Quellenüberschrift beschreibt einen möglichen Wechsel.")
        self.assertTrue(rewriter.validate_rewrite(BBC_TITLE, safe, evidence_scope="headline")[0])
        for detail in ["brasilianischen Spieler", "jungen Spieler", "Stürmer", "Spieler von Real Madrid", "Spieler aus der Akademie"]:
            with self.subTest(detail=detail):
                valid, reason = rewriter.validate_rewrite(BBC_TITLE, safe.replace("Spieler", detail), evidence_scope="headline")
                self.assertFalse(valid)
                self.assertIn("Unbelegte", reason)
        supported = BBC_TITLE.replace("Endrick", "Brazilian forward Endrick")
        translated = safe.replace("Spieler", "brasilianischen Stürmer")
        self.assertTrue(rewriter.validate_rewrite(supported, translated, evidence_scope="headline")[0])

    def test_single_player_explicit_transfer_interest_and_contract(self):
        cases = [
            ("Official: Florian Wirtz joins Liverpool", "FC Liverpool"),
            ("Florian Wirtz linked with Liverpool", "FC Liverpool"),
            ("Liverpool expected to revive interest in Bradley Barcola", "FC Liverpool"),
            ("Bayern interessiert sich für Florian Wirtz", "FC Bayern München"),
            ("Harry Kane: contract extension at Bayern", "FC Bayern München"),
        ]
        for title, target in cases:
            with self.subTest(title=title):
                result = assess_transfer_evidence(title)
                self.assertIsNone(result["reason"])
                self.assertEqual(result["club"], target)
                self.assertIsNone(result["from_club"])

    def test_two_club_direction_ignores_order_and_popularity(self):
        cases = [
            ("Florian Wirtz transfer from Real Madrid to Liverpool", "Real Madrid", "FC Liverpool"),
            ("Florian Wirtz transfer to Liverpool from Real Madrid", "Real Madrid", "FC Liverpool"),
            ("Florian Wirtz transfer from Liverpool to Real Madrid", "FC Liverpool", "Real Madrid"),
            ("Florian Wirtz wechselt von Bayern zu Liverpool", "FC Bayern München", "FC Liverpool"),
            ("Florian Wirtz wechselt zu Bayern von Liverpool", "FC Liverpool", "FC Bayern München"),
            ("Liverpool interested in Florian Wirtz from Bayern", "FC Bayern München", "FC Liverpool"),
            ("Bayern interessiert sich für Florian Wirtz von Liverpool", "FC Liverpool", "FC Bayern München"),
            ("Transfert: Florian Wirtz de Bayern à Liverpool", "FC Bayern München", "FC Liverpool"),
            ("Florian Wirtz: trasferimento dal Bayern al Liverpool", "FC Bayern München", "FC Liverpool"),
            ("Fichaje: Florian Wirtz desde Bayern a Liverpool", "FC Bayern München", "FC Liverpool"),
        ]
        for title, origin, target in cases:
            with self.subTest(title=title):
                result = assess_transfer_evidence(title)
                self.assertIsNone(result["reason"])
                self.assertEqual((result["from_club"], result["club"]), (origin, target))

    def test_rejects_ambiguous_entities_and_unproved_direction(self):
        cases = [
            ("Liverpool transfer interest in Florian Wirtz and Harry Kane", "ambiguous_players"),
            ("Florian Wirtz transfer: Liverpool and Bayern interested", "ambiguous_transfer_direction"),
            ("Florian Wirtz transfer to Liverpool or Bayern", "ambiguous_transfer_direction"),
            ("Florian Wirtz from Liverpool linked with Bayern and Barcelona", "ambiguous_clubs"),
            ("Florian Wirtz from Liverpool could make a transfer", "ambiguous_transfer_direction"),
            ("Florian Wirtz will not join Liverpool", "negated_transfer"),
        ]
        for title, reason in cases:
            with self.subTest(title=title):
                self.assertEqual(assess_transfer_evidence(title)["reason"], reason)

    def test_alias_boundaries_and_nested_names(self):
        self.assertEqual(assess_transfer_evidence("Official: Lionel Messi joins Inter Miami")["club"], "Inter Miami")
        self.assertEqual(assess_transfer_evidence("Florian Wirtz linked with Liverpool. Bayern wants Jamal Musiala.")["reason"], "ambiguous_players")
        # 'Inter' must not be inferred from 'interested', nor 'Tel' from unrelated words.
        result = assess_transfer_evidence("Liverpool interested in Florian Wirtz; hotel talks continue")
        self.assertIsNone(result["reason"])
        self.assertEqual(result["club"], "FC Liverpool")

    def test_named_rfc_feed_timezones(self):
        for zone, hour in [("CET", 11), ("CEST", 10), ("BST", 11), ("+0200", 10), ("GMT", 12)]:
            with self.subTest(zone=zone):
                self.assertEqual(parse_source_time(f"Sun, 20 Sep 2026 12:30:00 {zone}"),
                                 datetime(2026, 9, 20, hour, 30, tzinfo=timezone.utc))


class EvidencePipelineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = Database()
        self.pipeline = SpeedPipeline(self.db)
        self.pipeline._assign_article_image = AsyncMock()
        self.network = patch.object(socket.socket, "connect", side_effect=AssertionError("No networking"))
        self.network.start()
        self.addCleanup(self.network.stop)

    async def test_bbc_scope_propagates_to_story_article_and_real_rewrite_path(self):
        source = {"id": "bbc-gossip", "status": "pending", "created_at": utcnow(),
                  "headline_raw": BBC_TITLE, "summary": BBC_SUMMARY, "body_raw": BBC_SUMMARY,
                  "summary_raw": BBC_SUMMARY, "source_published_at": utcnow(), "source_name": "BBC Sport",
                  "source_url": "https://www.bbc.co.uk/sport/football/articles/cq1j478n0ll7o"}
        await self.db.events.insert_one(source)
        await self.pipeline.process_pending_events(1)
        stored_event = await self.db.events.find_one({"id": source["id"]})
        self.assertEqual(stored_event["summary"], BBC_SUMMARY)
        self.assertEqual(stored_event["body_raw"], BBC_SUMMARY)
        article = await self.db.articles.find_one({})
        story = await self.db.transfer_stories.find_one({})
        self.assertEqual(article["evidence_scope"], "headline")
        self.assertEqual(article["source_summary"], "")
        self.assertEqual(story["sources"][0]["raw_summary"], "")
        self.assertEqual(article["source_headline"], BBC_TITLE)
        self.assertNotIn("Haaland", article["body"])
        self.assertEqual(article["transfer_status"], "rumor")

        # A previous body and metadata must not become source facts on a retry.
        await self.db.articles.update_one({"id": article["id"]}, {"$set": {
            "body": "HISTORICAL_BODY: Real Madrid paid 999 million euros.",
            "source_summary": BBC_SUMMARY, "current_club": "HISTORICAL_CLUB", "player_age": 99}})
        context = types.ModuleType("context_scraper")
        context.get_context_service = unittest.mock.Mock(side_effect=AssertionError("Context must not be loaded"))
        research = types.ModuleType("context_research")
        research.get_context_researcher = unittest.mock.Mock(side_effect=AssertionError("Fallback must not be loaded"))
        good = ("## Endrick im Gespräch\nBBC Sport berichtet, dass Arsenal im Januar einen Vorstoß für Endrick erwägen könnte. "
                "Die Überschrift der Gerüchterundschau beschreibt damit eine mögliche Entwicklung und keinen bestätigten Wechsel.")
        seen = []
        async def complete(**kwargs):
            prompt = "\n".join(message["content"] for message in kwargs["messages"])
            seen.append(prompt)
            for excluded in ["HISTORICAL", "Real Madrid", "Haaland", "Wirtz", "Liverpool", "mindestens 150", "5 Absätze"]:
                self.assertNotIn(excluded, prompt)
            self.assertIn(BBC_TITLE, prompt)
            text = good + " Die Ablöse beträgt 999 Millionen Euro." if len(seen) == 1 else good
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=text))])
        client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(
            create=AsyncMock(side_effect=complete))), close=AsyncMock())
        with patch.dict(os.environ, {"OPENAI_API_KEY": "offline-fixture"}), patch.dict(sys.modules, {
                "context_scraper": context, "context_research": research}), patch("openai.AsyncOpenAI", return_value=client):
            self.assertTrue(await GPTRewriter(self.db).rewrite_article(article["id"]))
        self.assertEqual(len(seen), 2)
        context.get_context_service.assert_not_called()
        research.get_context_researcher.assert_not_called()
        client.close.assert_awaited_once()
        rewritten = await self.db.articles.find_one({"id": article["id"]})
        self.assertEqual(rewritten["body"], good)
        self.assertEqual(rewritten["source_summary"], "")
        self.assertFalse(rewritten["has_researched_context"])

    async def test_full_source_update_to_headline_clears_persisted_summary(self):
        event = {"id": "full", "headline_raw": "Arsenal may move for Endrick", "summary": "Arsenal are interested in Endrick.",
                 "source_name": "BBC Sport", "source_url": "https://source.invalid/first", "source_published_at": utcnow()}
        await self.pipeline.process_event(event)
        self.assertEqual((await self.db.articles.find_one({}))["evidence_scope"], "full")
        await self.pipeline.process_event({**event, "id": "roundup", "source_url": "https://source.invalid/second",
                                           "headline_raw": BBC_TITLE, "summary": BBC_SUMMARY, "body_raw": BBC_SUMMARY})
        self.assertEqual(await self.db.articles.count_documents({}), 1)
        article = await self.db.articles.find_one({})
        self.assertEqual((article["evidence_scope"], article["source_summary"]), ("headline", ""))
        self.assertNotIn("Haaland", article["body"])

    async def test_non_transfer_and_ambiguous_reports_never_create_story_or_article(self):
        titles = [
            "Darts: Luke Littler accepts million pound offer",
            "Golf: record million prize officially confirmed",
            "Lionel Messi joins Barcelona charity match for millions",
            "Barcelona medical update: Christensen injury confirmed",
            "Messi scores as Barcelona defeats Liverpool",
            "Barcelona to pay Lionel Messi 4.7 million per match",
            "Official: Messi medical at Barcelona",
            "Liverpool transfer interest in Florian Wirtz and Harry Kane",
            "Florian Wirtz transfer: Liverpool and Bayern interested",
        ]
        for index, title in enumerate(titles):
            await self.db.events.insert_one({"id": f"e{index}", "status": "pending", "headline_raw": title,
                                             "source_published_at": utcnow(), "created_at": utcnow()})
        result = await self.pipeline.process_pending_events(len(titles))
        self.assertEqual(result["review"], len(titles))
        self.assertEqual(await self.db.events.count_documents({"status": "review"}), len(titles))
        self.assertEqual(await self.db.transfer_stories.count_documents({}), 0)
        self.assertEqual(await self.db.articles.count_documents({}), 0)
        self.assertEqual(await self.db.pipeline_locks.count_documents({}), 0)

    async def test_pipeline_persists_evidenced_target_not_popular_club(self):
        result = await self.pipeline.process_event({"id": "direction", "headline_raw":
            "Official: Florian Wirtz transfer from Real Madrid to Liverpool", "source_published_at": utcnow(),
            "source_name": "Source A", "source_url": "https://source.invalid/direction"})
        self.assertEqual(result["action"], "created")
        article = await self.db.articles.find_one({})
        story = await self.db.transfer_stories.find_one({})
        self.assertEqual(article["club_name"], "FC Liverpool")
        self.assertEqual(article["from_club"], "Real Madrid")
        self.assertEqual(story["target_club"], "FC Liverpool")


if __name__ == "__main__":
    unittest.main()
