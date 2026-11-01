"""An English headline and lead must agree on the moving player and destination."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entity_catalogue import build_entity_catalogues
from source_rewrite_checks import validate_source_rewrite
from source_scope import apply_evidence_scope
from transfer_evidence import assess_transfer_evidence


TITLE = "Retired Town Utd legend Keller signs for Riverton"
CLAIM = "Robin Keller comes out of retirement to join Northern Premier League side AFC Riverton & Vale"
SUMMARY = ("Former Leeds United and Bolton Wanderers striker " + CLAIM
           + " as they prepare for their FA Cup match against West Ham United.")


class EnglishSigningEvidenceTests(unittest.TestCase):
    def test_one_verified_actor_and_destination_with_original_source_span(self):
        result = assess_transfer_evidence(TITLE, SUMMARY)
        scoped = apply_evidence_scope({"title": TITLE, "summary": SUMMARY}, result)
        self.assertEqual((result["player"], result["club"], result["from_club"]),
                         ("Robin Keller", "AFC Riverton & Vale", None))
        self.assertEqual((scoped["evidence_scope"], scoped["verified_stage"], scoped["title"], scoped["summary"]),
                         ("claim", "done", "Keller signs for Riverton\n" + CLAIM, ""))
        self.assertEqual(scoped["original_source_headline"], TITLE)

    def test_plain_signing_without_retirement_also_uses_the_named_destination(self):
        result = assess_transfer_evidence("Jordan Mills signs for FC Westhaven",
                                          "Jordan Mills has signed for FC Westhaven.")
        self.assertEqual((result["player"], result["club"], result["verified_stage"]),
                         ("Jordan Mills", "FC Westhaven", "done"))

    def test_does_not_assign_another_actor_destination_or_competing_claim(self):
        alternatives = [
            (TITLE.replace("Keller", "Parker"), SUMMARY),
            (TITLE.replace("Riverton", "West Ham United"), SUMMARY),
            (TITLE, SUMMARY.replace("AFC Riverton & Vale", "FC Newbridge")),
            (TITLE, SUMMARY.replace("Robin Keller", "the unnamed player")),
            (TITLE, SUMMARY.replace("AFC Riverton & Vale", "Riverton")),
            (TITLE, SUMMARY.replace("AFC Riverton & Vale", "AFC Riverton or FC Newbridge")),
            (TITLE, SUMMARY.replace("comes out", "could come out")),
            (TITLE, SUMMARY.replace("comes out", "will not come out")),
            (TITLE + "?", SUMMARY),
            (TITLE, SUMMARY + " The report was denied."),
            (TITLE, SUMMARY + " If a deal is reached, he could sign."),
            (TITLE, SUMMARY.replace("join", "coach")),
        ]
        for title, summary in alternatives:
            with self.subTest(title=title, summary=summary):
                self.assertIsNotNone(assess_transfer_evidence(title, summary)["reason"])

    def test_conflicting_short_club_alias_cannot_establish_the_full_destination(self):
        cats = build_entity_catalogues(clubs=[{"name": "Riverton Town", "short_name": "Riverton"}])
        self.assertIsNotNone(assess_transfer_evidence(TITLE, SUMMARY, cats)["reason"])

    def test_conflicting_short_player_alias_is_not_a_new_identity(self):
        cats = build_entity_catalogues(players=[{"full_name": "Max Keller", "short_name": "Keller"}])
        self.assertIsNotNone(assess_transfer_evidence(TITLE, SUMMARY, cats)["reason"])

    def test_translation_of_signs_requires_verified_confirmation_for_that_player_and_club(self):
        result = assess_transfer_evidence(TITLE, SUMMARY)
        article = {"evidence_scope": "claim", "transfer_status": "done", "source_name": "BBC Sport",
                   "transfer_type": "permanent", "source_headline": result["evidence_headline"],
                   "evidence_spans": result["evidence_spans"], "player_name": "Robin Keller",
                   "club_name": "AFC Riverton & Vale"}
        body = "Laut BBC Sport wechselt Robin Keller zu AFC Riverton & Vale."
        self.assertTrue(validate_source_rewrite(body, article)[0])
        for wrong in (body.replace("Robin Keller", "Max Keller"), body.replace("AFC Riverton & Vale", "Burton Albion"),
                      body + " Der Verein hat das offiziell bestätigt."):
            with self.subTest(rewrite=wrong):
                self.assertFalse(validate_source_rewrite(wrong, article)[0])
        for change in ({"transfer_status": "rumor"}, {"club_name": "West Ham United"},
                       {"player_name": "Another Player"}, {"evidence_scope": "headline"},
                       {"evidence_spans": [None, None]}, {"evidence_spans": []},
                       {"source_headline": result["evidence_headline"].replace("signs", "might sign")}):
            with self.subTest(change=change):
                self.assertFalse(validate_source_rewrite(body, {**article, **change})[0])


if __name__ == "__main__":
    unittest.main()
