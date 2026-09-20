"""Offline regressions for evidence-based direction and pre-write review decisions."""
from datetime import datetime, timezone
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline_state import parse_source_time, utcnow
from speed_pipeline import SpeedPipeline
from transfer_evidence import assess_transfer_evidence
from test_pipeline_repair import Database


class EvidenceTests(unittest.TestCase):
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
