"""A partial name in a Foot Mercato report must not license another player."""
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entity_catalogue import build_entity_catalogues
from entity_recognition import EntityRecognizer
from transfer_evidence import assess_transfer_evidence, unsupported_headline_detail


TITLE = "Le PSG n’a formulé aucune offre pour JJ Gabriel !"
INTRO = ("Alors que JJ Gabriel, jeune attaquant de 16 ans appartenant à Manchester United, fait "
         "actuellement beaucoup parler de lui sur le marché des transferts, son nom a notamment été associé à plusieurs (…)")
OLD_RECORD = {"full_name": "Gabriel Magalhães", "name": "Gabriel", "short_name": "GABRIEL", "aliases": ["Gabriel"]}


class GabrielIdentityTests(unittest.TestCase):
    def test_incomplete_foot_mercato_report_cannot_become_a_magalhaes_story(self):
        for cat in (None, build_entity_catalogues(), build_entity_catalogues(players=[OLD_RECORD])):
            result = assess_transfer_evidence(TITLE, INTRO, cat)
            self.assertIsNotNone(result["reason"])
            self.assertNotIn("player", result)
            self.assertIsNotNone(unsupported_headline_detail(
                "Gabriel Magalhães spielt bei Manchester United.", TITLE + "\n" + INTRO, cat))

    def test_old_database_alias_cannot_authorize_even_a_positive_transfer_claim(self):
        cat = build_entity_catalogues(players=[OLD_RECORD])
        self.assertNotIn("gabriel", cat["players"])
        self.assertIn("gabriel", cat["ambiguous_players"])
        for identity in ("Gabriel", "JJ Gabriel", "J.J. Gabriel"):
            for catalogue in (None, cat):
                with self.subTest(identity=identity, database=bool(catalogue)):
                    self.assertEqual(assess_transfer_evidence(
                        f"{identity} joins Liverpool", catalogues=catalogue), {"reason": "ambiguous_players"})
        self.assertIsNone(EntityRecognizer().recognize_player("JJ Gabriel"))

    def test_unambiguous_full_names_work_including_registered_jj(self):
        cat = build_entity_catalogues(players=[OLD_RECORD, {"name": "JJ Gabriel", "aliases": ["Gabriel"]}])
        for explicit, expected in (("Gabriel Magalhães", "Gabriel Magalhães"), ("Gabriel Magalhaes", "Gabriel Magalhães"),
                                   ("Gabriel Martinelli", "Gabriel Martinelli"), ("JJ Gabriel", "JJ Gabriel")):
            with self.subTest(explicit=explicit):
                r = assess_transfer_evidence(f"{explicit} joins Liverpool", catalogues=cat)
                self.assertEqual((r["reason"], r["player"], r["club"]), (None, expected, "FC Liverpool"))
                if explicit != "JJ Gabriel":
                    self.assertEqual(assess_transfer_evidence(f"{explicit} joins Liverpool")["player"], expected)
        self.assertEqual(EntityRecognizer().recognize_player("Gabriel Magalhães").name, "Gabriel Magalhães")
        self.assertIsNone(unsupported_headline_detail(
            "Gabriel Magalhães soll zu Liverpool wechseln.", "Gabriel Magalhaes joins Liverpool", cat))


class GabrielArticleGateTests(unittest.IsolatedAsyncioTestCase):
    async def test_event_is_retained_for_review_without_creating_a_story_or_draft(self):
        from pipeline_state import utcnow
        from speed_pipeline import SpeedPipeline
        from test_pipeline_repair import Database

        db = Database()
        await db.players.insert_one(dict(OLD_RECORD))
        await db.events.insert_one({"id": "jj-fixture", "status": "pending", "created_at": utcnow(),
            "source_published_at": utcnow(), "headline_raw": TITLE, "body_raw": INTRO,
            "source_name": "Foot Mercato", "source_url": "https://www.footmercato.net/fixture"})
        with patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
            outcome = await SpeedPipeline(db).process_pending_events(1)
        self.assertEqual((outcome["processed"], outcome["review"], outcome["errors"]), (1, 1, []))
        self.assertEqual((await db.events.find_one({"id": "jj-fixture"}))["status"], "review")
        self.assertEqual(await db.transfer_stories.count_documents({}), 0)
        self.assertEqual(await db.articles.count_documents({}), 0)


if __name__ == "__main__":
    unittest.main()
