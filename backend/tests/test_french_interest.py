"""Reported French interest needs the full player, explicit club and supporting sentence."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entity_catalogue import build_entity_catalogues
from source_rewrite_checks import validate_source_rewrite
from transfer_evidence import assess_transfer_evidence, unsupported_headline_detail


class FrenchInterestTests(unittest.TestCase):
    title = "Al-Ittihad se positionne sur Abdoul Koné"

    def test_full_name_wins_over_other_player_with_same_surname(self):
        catalogue = build_entity_catalogues(players=[{"name": "Manu Koné", "aliases": ["Koné"]}])
        body = ("Abdoul Koné plaît en Arabie saoudite. Selon nos informations, Al-Ittihad est intéressé "
                "par le défenseur du RB Leipzig. Formé au Stade de Reims, le joueur de (…)")
        evidence = assess_transfer_evidence(self.title, body, catalogue)
        self.assertEqual((evidence["player"], evidence["club"], evidence["from_club"], evidence["verified_stage"]),
                         ("Abdoul Koné", "Al-Ittihad", None, "rumor"))
        self.assertEqual(evidence["relation"], "interest")
        for span in evidence["evidence_spans"]:
            original = self.title if span["field"] == "headline" else body
            self.assertEqual(span["text"], original[span["start"]:span["end"]])
        self.assertNotIn("Reims", evidence["evidence_headline"])
        self.assertIsNotNone(unsupported_headline_detail("Manu Koné und Abdoul Koné", evidence["evidence_headline"], catalogue))

    def test_another_report_with_names_and_no_anaphora(self):
        title = "Arsenal se positionne sur Karim Dubois"
        result = assess_transfer_evidence(title, "Selon nos informations, Arsenal est intéressé par Karim Dubois.")
        self.assertEqual((result["player"], result["club"], result["verified_stage"]), ("Karim Dubois", "FC Arsenal", "rumor"))

    def test_german_copy_keeps_player_interested_club_and_employer_in_their_source_roles(self):
        body = ("Abdoul Koné plaît en Arabie saoudite. Selon nos informations, Al-Ittihad est intéressé "
                "par le défenseur du RB Leipzig.")
        result = assess_transfer_evidence(self.title, body)
        article = {"evidence_scope": "claim", "transfer_status": "rumor", "source_name": "Foot Mercato",
                   "original_source_headline": self.title, "source_headline": result["evidence_headline"],
                   "evidence_spans": result["evidence_spans"],
                   "player_name": result["player"], "club_name": result["club"], "transfer_type": "permanent"}
        heading = "## Abdoul Koné im Fokus von Al-Ittihad"
        sentence = "Laut Foot Mercato soll Al-Ittihad an Abdoul Koné interessiert sein."
        correct = heading + "\n\n" + sentence
        self.assertTrue(validate_source_rewrite(correct, article)[0])
        self.assertTrue(validate_source_rewrite(correct + " Dem Bericht zufolge spielt der Verteidiger bei RB Leipzig.", article)[0])
        for output in (
            heading + "\n\nLaut Foot Mercato soll Abdoul Koné an Al-Ittihad interessiert sein.",
            heading + "\n\nLaut Foot Mercato hat RB Leipzig Interesse an Abdoul Koné.",
            correct + " Auch RB Leipzig hat Interesse an Abdoul Koné.", correct + " Er wechselt zu Al-Ittihad.",
            correct + " Al-Ittihad verhandelt über die Ablöse.", correct + " Der Spieler unterschreibt einen Vertrag.",
            correct + " Al-Ittihad beabsichtigt eine Leihe.", correct + " Dem Bericht zufolge spielt der Verteidiger bei Al-Ittihad.",
            "## Abdoul Koné zeigt Interesse an Al-Ittihad\n\n" + sentence,
        ):
            with self.subTest(output=output):
                self.assertFalse(validate_source_rewrite(output, article)[0])
        self.assertFalse(validate_source_rewrite(correct, {**article, "club_name": "RB Leipzig"})[0])
        self.assertFalse(validate_source_rewrite(correct, {**article, "original_source_headline": "Changed"})[0])
        self.assertFalse(validate_source_rewrite(correct, {**article, "evidence_spans": []})[0])

    def test_unsupported_interest_stays_in_review(self):
        direct = "Al-Ittihad est intéressé par Abdoul Koné."
        for title, body in (
            (self.title, ""), (self.title + " ?", direct),
            (self.title, "Arsenal est intéressé par Abdoul Koné."),
            (self.title, "Al-Ittihad est intéressé par Manu Koné."),
            (self.title, "Al-Ittihad est intéressé par le défenseur du RB Leipzig."),
            (self.title, "Manu Koné plaît en Arabie saoudite. Al-Ittihad est intéressé par le défenseur du RB Leipzig."),
            (self.title, "Abdoul Koné plaît en Arabie saoudite. Al-Ittihad est intéressé par le défenseur du FC Inconnu."),
            (self.title, "Al-Ittihad serait intéressé par Abdoul Koné."), (self.title, "Al-Ittihad ne serait pas intéressé par Abdoul Koné."),
            (self.title, direct + " Le club renonce au dossier."), (self.title, direct + " Mais seulement si un joueur part."),
            (self.title, direct + " Arsenal est aussi intéressé par Abdoul Koné."),
            ("FC Inconnu se positionne sur Abdoul Koné", "FC Inconnu est intéressé par Abdoul Koné."),
            ("Al-Ittihad se positionne sur Koné", direct),
        ):
            with self.subTest(title=title, body=body):
                self.assertIsNotNone(assess_transfer_evidence(title, body)["reason"])
