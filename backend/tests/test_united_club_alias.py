"""Offline regression for the BBC Leeds renewal misidentified as Manchester."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entity_catalogue import build_entity_catalogues
from entity_recognition import CLUBS_DB, EntityRecognizer
from transfer_evidence import assess_transfer_evidence, unsupported_headline_detail


BBC_TITLE = "Calvert-Lewin set for new Leeds deal"
BBC_SUMMARY = "England striker Dominic Calvert-Lewin is set to sign a new contract at Leeds United."


class UnitedClubAliasTests(unittest.TestCase):
    def catalogue_variants(self):
        return [None, build_entity_catalogues(), build_entity_catalogues(clubs=[
            {"name": "Manchester United", "short_name": "United", "aliases": ["UNITED"]},
        ])]

    def test_actual_bbc_renewal_resolves_only_source_named_leeds(self):
        for catalogue in self.catalogue_variants():
            with self.subTest(catalogue=catalogue is not None):
                result = assess_transfer_evidence(BBC_TITLE, BBC_SUMMARY, catalogue)
                self.assertEqual(result["reason"], None)
                self.assertEqual((result["player"], result["club"], result["from_club"],
                                  result["transfer_type"], result["evidence_scope"]),
                                 ("Dominic Calvert-Lewin", "Leeds United", None, "extension", "full"))

    def test_static_recognizer_no_longer_expands_united_to_manchester(self):
        self.assertNotIn("united", CLUBS_DB)
        recognizer = EntityRecognizer()
        self.assertIsNone(recognizer.recognize_club("United"))
        self.assertEqual(recognizer.recognize_club("Leeds United").canonical_name, "Leeds United")

    def test_database_alias_cannot_reintroduce_shared_name(self):
        for field in ("name", "short_name", "aliases"):
            with self.subTest(field=field):
                record = {"name": "Manchester United", "full_name": "Manchester United",
                          field: [" United "] if field == "aliases" else " United "}
                catalogue = build_entity_catalogues(clubs=[record])
                self.assertNotIn("united", catalogue["clubs"])
                self.assertIn("united", catalogue["ambiguous_clubs"])
                self.assertEqual(assess_transfer_evidence(
                    "Florian Wirtz joins United", catalogues=catalogue)["reason"], "ambiguous_clubs")

    def test_standalone_and_unknown_prefixed_united_do_not_guess_a_club(self):
        for title in ("Florian Wirtz joins United", "Florian Wirtz joins Oxford United",
                      "Florian Wirtz joins Sheffield United"):
            for catalogue in self.catalogue_variants():
                with self.subTest(title=title, catalogue=catalogue is not None):
                    self.assertIsNotNone(assess_transfer_evidence(title, catalogues=catalogue)["reason"])

    def test_full_known_names_still_disambiguate_shared_suffix(self):
        for alias, expected in (("Manchester United", "Manchester United"), ("Man United", "Manchester United"),
                                ("Man Utd", "Manchester United"), ("Newcastle United", "Newcastle United"),
                                ("West Ham United", "West Ham United"), ("Leeds United", "Leeds United"),
                                ("Leeds", "Leeds United")):
            with self.subTest(alias=alias):
                result = assess_transfer_evidence(f"Florian Wirtz joins {alias}", catalogues=build_entity_catalogues())
                self.assertEqual((result["reason"], result["club"]), (None, expected))

    def test_unresolved_united_cannot_disappear_next_to_a_known_club(self):
        for title in ("Florian Wirtz contract extension at Liverpool and United",
                      "Florian Wirtz contract extension at Liverpool and Oxford United",
                      "Florian Wirtz transfer from United to Leeds",
                      "Florian Wirtz transfer from Sheffield United to Leeds"):
            for catalogue in self.catalogue_variants():
                with self.subTest(title=title, catalogue=catalogue is not None):
                    self.assertEqual(assess_transfer_evidence(title, catalogues=catalogue)["reason"],
                                     "ambiguous_clubs")

    def test_known_united_clubs_preserve_explicit_transfer_direction(self):
        result = assess_transfer_evidence("Florian Wirtz transfer from Manchester United to Leeds United",
                                          catalogues=build_entity_catalogues())
        self.assertEqual((result["reason"], result["from_club"], result["club"]),
                         (None, "Manchester United", "Leeds United"))

    def test_rewrite_cannot_turn_source_leeds_into_manchester(self):
        for catalogue in self.catalogue_variants():
            with self.subTest(catalogue=catalogue is not None):
                self.assertIsNotNone(unsupported_headline_detail(
                    "Dominic Calvert-Lewin bei Manchester United im Gespräch", BBC_TITLE + "\n" + BBC_SUMMARY,
                    catalogue))
                self.assertIsNone(unsupported_headline_detail(
                    "Dominic Calvert-Lewin steht vor einem neuen Vertrag bei Leeds United.",
                    BBC_TITLE + "\n" + BBC_SUMMARY, catalogue))

    def test_unrecognized_united_source_does_not_license_manchester_rewrite(self):
        for source in ("Florian Wirtz joins United", "Florian Wirtz joins Oxford United"):
            for catalogue in self.catalogue_variants():
                with self.subTest(source=source, catalogue=catalogue is not None):
                    self.assertIsNotNone(unsupported_headline_detail(
                        "Florian Wirtz joins Manchester United", source, catalogue))


if __name__ == "__main__":
    unittest.main()
