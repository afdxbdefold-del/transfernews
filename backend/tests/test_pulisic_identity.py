"""The full spellings in Foot Mercato's 30 October renewal identify one player."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entity_catalogue import build_entity_catalogues
from transfer_evidence import assess_transfer_evidence


class PulisicIdentityTests(unittest.TestCase):
    def test_accented_and_ascii_full_names_share_only_the_existing_identity(self):
        title = "AC Milan : Christian Pulišić prolonge jusqu’en 2031"
        summary = ("C’est désormais officiel : Christian Pulisic poursuit son aventure avec l’AC Milan. "
                   "Le club lombard a annoncé ce vendredi la prolongation de contrat de "
                   "l’international américain jusqu’au 30 juin 2031. (…)")
        for cat in (None, build_entity_catalogues()):
            with self.subTest(using_database=cat is not None):
                result = assess_transfer_evidence(title, summary, cat)
                self.assertEqual((result["player"], result["club"], result["transfer_type"]),
                                 ("Christian Pulisic", "AC Milan", "extension"))
                other = assess_transfer_evidence("Mateo Pulišić joins Liverpool", catalogues=cat)
                self.assertEqual(other["player"], "Mateo Pulišić")
        self.assertNotIn("pulišić", build_entity_catalogues()["players"])

    def test_database_claim_held_when_another_identity_owns_the_same_full_alias(self):
        cat = build_entity_catalogues(players=[{"name": "Another Player", "aliases": ["Christian Pulišić"]}])
        self.assertIn("christian pulišić", cat["ambiguous_players"])
        self.assertNotIn("christian pulišić", cat["players"])
        self.assertEqual(assess_transfer_evidence("Christian Pulišić joins Liverpool", catalogues=cat),
                         {"reason": "ambiguous_players"})
