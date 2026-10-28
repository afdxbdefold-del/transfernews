"""Exact provenance and context isolation before any story or rewrite writes."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_scope import apply_evidence_scope


class SourceScopeTests(unittest.TestCase):
    def setUp(self):
        self.claim = "Morris Schröter unterschreibt beim FSV Zwickau bis 2028."
        self.event = {"title": "Ein neuer Spieler", "headline_raw": "Ein neuer Spieler",
                      "summary": self.claim + " Trainer Mikel Arteta sprach über Arsenal.",
                      "body_raw": "unrelated fallback", "summary_raw": "another fallback"}
        self.evidence = {"evidence_scope": "claim", "evidence_headline": self.claim,
                         "verified_stage": "official", "evidence_spans": [
                             {"field": "summary", "start": 0, "end": len(self.claim), "text": self.claim}]}

    def test_isolates_exact_claim_and_retains_audit_provenance_without_mutation(self):
        original = copy.deepcopy(self.event)
        result = apply_evidence_scope(self.event, self.evidence)
        self.assertEqual(self.event, original)
        self.assertEqual(result["title"], self.claim)
        self.assertEqual(result["headline_raw"], self.claim)
        self.assertEqual(result["original_source_headline"], original["title"])
        for key in ("summary", "body_raw", "summary_raw"):
            self.assertEqual(result[key], "")
        self.assertEqual(result["verified_stage"], "official")
        self.assertEqual(result["evidence_spans"], self.evidence["evidence_spans"])
        result["evidence_spans"][0]["text"] = "changed"
        self.assertEqual(self.evidence["evidence_spans"][0]["text"], self.claim)

    def test_rejects_unverifiable_or_forged_claim(self):
        bad_cases = [
            {"evidence_headline": self.claim.replace("2028", "2030")},
            {"evidence_spans": []},
            {"evidence_scope": "unchecked"},
            {"verified_stage": "confirmed_by_model"},
            {"evidence_spans": [{"field": "body", "start": 0, "end": len(self.claim), "text": self.claim}]},
            {"evidence_spans": [{"field": "summary", "start": -1, "end": len(self.claim), "text": self.claim}]},
            {"evidence_spans": [{"field": "summary", "start": False, "end": len(self.claim), "text": self.claim}]},
            {"evidence_spans": [{"field": "summary", "start": 0, "end": len(self.claim), "text": self.claim.replace("2028", "2030")}]},
        ]
        for changes in bad_cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                apply_evidence_scope(self.event, {**self.evidence, **changes})

    def test_multiple_source_spans_have_fixed_join_without_generated_connectors(self):
        title = self.event["title"]
        spans = [{"field": "headline", "start": 0, "end": len(title), "text": title},
                 self.evidence["evidence_spans"][0]]
        evidence = {**self.evidence, "evidence_spans": spans,
                    "evidence_headline": title + "\n" + self.claim}
        self.assertEqual(apply_evidence_scope(self.event, evidence)["title"], title + "\n" + self.claim)

    def test_unverified_import_fields_cannot_upgrade_a_normal_report(self):
        event = {**self.event, "verified_stage": "official", "evidence_spans": ["forged"]}
        result = apply_evidence_scope(event, {"evidence_scope": "full"})
        self.assertNotIn("verified_stage", result)
        self.assertNotIn("evidence_spans", result)


if __name__ == "__main__":
    unittest.main()
