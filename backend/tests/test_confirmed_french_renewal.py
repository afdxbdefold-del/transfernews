"""A completed contract needs positive evidence at processing and rewrite time."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_rewrite_checks import validate_source_rewrite
from source_scope import apply_evidence_scope


PLAYER = "Christian Pulisic"
CLUB = "AC Milan"
TITLE = "AC Milan : Christian Pulišić prolonge jusqu’en 2031"
INTRO = ("C’est désormais officiel : Christian Pulisic poursuit son aventure avec l’AC Milan. "
         "Le club lombard a annoncé ce vendredi la prolongation de contrat de l’international "
         "américain jusqu’au 30 juin 2031. (…)")
REWRITE = ("Laut Foot Mercato hat die AC Milan den Vertrag mit Christian Pulisic verlängert. "
           "Der Vertrag läuft bis zum 30. Juni 2031.")


class ConfirmedFrenchRenewalTests(unittest.TestCase):
    def check(self, title, summary, player=PLAYER, club=CLUB, rewrite=REWRITE):
        source = {"title": title, "summary": summary}
        evidence = {"evidence_scope": "full", "player": player, "club": club, "transfer_type": "extension"}
        event = apply_evidence_scope(source, evidence)
        article = {"source_headline": title, "source_summary": summary, "source_name": "Foot Mercato",
                   "transfer_type": "extension", "player_name": player, "club_name": club,
                   "transfer_status": "official", "evidence_scope": "full"}
        return event.get("verified_stage"), validate_source_rewrite(rewrite, article)

    def test_actual_announcement_supports_completed_renewal(self):
        self.assertEqual(self.check(TITLE, INTRO), ("official", (True, "OK")))
        self.assertEqual(self.check(
            "Lyon : Marie Dupont prolonge son contrat jusqu'en 2029",
            "Lyon a confirmé la prolongation du contrat de Marie Dupont jusqu’en 2029.",
            "Marie Dupont", "Lyon", "Laut Foot Mercato hat Lyon den Vertrag mit Marie Dupont verlängert."),
            ("official", (True, "OK")))

    def test_qualifications_identity_date_and_source_scope_must_all_match(self):
        cases = (
            (TITLE + " ?", INTRO),
            (TITLE.replace("prolonge", "pourrait prolonger"), INTRO),
            (TITLE, INTRO.replace("désormais officiel", "bientôt officiel")),
            (TITLE, INTRO.replace("a annoncé", "n’a pas annoncé")),
            (TITLE, INTRO.replace("la prolongation", "des discussions sur la prolongation")),
            (TITLE, INTRO.replace("a annoncé", "aurait annoncé")),
            (TITLE, INTRO.replace("a annoncé", "annoncera")),
            (TITLE, INTRO.replace("Christian Pulisic", "Harry Kane")),
            (TITLE, INTRO.replace("AC Milan", "Inter Milan")),
            (TITLE, INTRO.replace("30 juin 2031", "30 juin 2029")),
            (TITLE, INTRO + " Son agent dément la prolongation."),
            (TITLE, INTRO.split(". ")[0] + "."),
            (TITLE, ""),
        )
        for title, summary in cases:
            with self.subTest(title=title, summary=summary):
                self.assertEqual(self.check(title, summary), (None, (False, "unsupported_completion_claim")))

    def test_completion_does_not_justify_a_signature_or_a_new_club(self):
        for addition, reason in ((" Er hat den Vertrag unterschrieben.", "unsupported_signature_claim"),
                                 (" Er wechselt zur AC Milan.", "renewal_changed_to_transfer")):
            with self.subTest(reason=reason):
                self.assertEqual(self.check(TITLE, INTRO, rewrite=REWRITE + addition),
                                 ("official", (False, reason)))
