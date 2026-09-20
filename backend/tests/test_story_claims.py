import unittest

from story_engine import StoryEngine


class StoryClaimTests(unittest.TestCase):
    def setUp(self):
        self.engine = StoryEngine(None)

    def test_confirmation_of_interest_is_not_a_completed_transfer(self):
        for title in (
            "Journalist confirmed Liverpool are expected to revive interest in Endrick",
            "Arsenal confirmed interest in signing Endrick",
            "Wirtz has signed for Arsenal?",
            "Arsenal could announce official Wirtz transfer",
            "Der Wechsel von Wirtz ist noch nicht offiziell",
        ):
            with self.subTest(title=title):
                self.assertNotIn(self.engine._detect_stage(title), {"official", "done", "near_done"})

    def test_past_signing_in_summary_does_not_promote_current_rumor(self):
        result = self.engine.extract_entities(
            "Arsenal interested in Endrick",
            "Real Madrid confirmed his transfer in 2024. Arsenal could now move for him.",
            "BBC Sport",
        )
        self.assertEqual(result["stage"], "rumor")

    def test_explicit_current_confirmation_remains_official(self):
        self.assertEqual(self.engine._detect_stage("Arsenal confirms: Wirtz has signed for the club"), "official")
        self.assertEqual(self.engine._detect_stage("Arsenal verpflichtet Wirtz offiziell"), "official")

    def test_extension_and_loan_headlines_preserve_transaction_type(self):
        extension = self.engine.generate_headline("Wirtz", "Arsenal", "official", "extension")
        self.assertEqual(extension, "Wirtz verlängert Vertrag bei Arsenal")
        rumor = self.engine.generate_headline("Wirtz", "Arsenal", "rumor", "extension")
        self.assertIn("im Gespräch", rumor)
        loan = self.engine.generate_headline("Wirtz", "Arsenal", "official", "loan")
        self.assertIn("auf Leihbasis", loan)


if __name__ == "__main__":
    unittest.main()
