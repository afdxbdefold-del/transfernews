"""Actual October RSS claims and conservative renewal counterexamples; offline."""
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entity_catalogue import build_entity_catalogues
from transfer_evidence import assess_transfer_evidence


SKY_TITLE = "'Bellingham agrees new five-year deal at Real Madrid'"
BBC_TITLE = "Bellingham agrees new Real deal - Saturday's gossip"
BBC_SUMMARY = (
    "Real Madrid midfielder Jude Bellingham ready to commit his future to La Liga club, "
    "Arsenal and Liverpool told price for Brentford's Kevin Schade, Man Utd and Chelsea "
    "among clubs monitoring Jules Kounde's future at Barcelona, plus more."
)
FRENCH_TITLE = "Le Real Madrid a bouclé la prolongation de Jude Bellingham"
FRENCH_SUMMARY = (
    "Jude Bellingham et le Real Madrid ont trouvé un accord pour prolonger leur collaboration "
    "jusqu’au 30 juin 2031, selon AS. Arrivé à l’été 2023 en provenance du Borussia Dortmund, "
    "l’international (…)"
)


class RenewalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.catalogues = build_entity_catalogues()
        guard = patch.object(socket.socket, "connect", side_effect=AssertionError("No networking"))
        guard.start()
        self.addCleanup(guard.stop)

    def assert_renewal(self, title, summary="", player="Jude Bellingham", club="Real Madrid", scope="headline"):
        result = assess_transfer_evidence(title, summary, self.catalogues)
        self.assertIsNone(result["reason"], result)
        self.assertEqual((result["player"], result["club"], result["from_club"],
                          result["transfer_type"], result["evidence_scope"]),
                         (player, club, None, "extension", scope))

    def test_actual_sky_contract_headline_with_empty_summary(self):
        self.assert_renewal(SKY_TITLE)

    def test_actual_bbc_roundup_discards_other_players(self):
        self.assert_renewal(BBC_TITLE, BBC_SUMMARY)

    def test_actual_french_renewal_discards_historical_club(self):
        self.assert_renewal(FRENCH_TITLE, FRENCH_SUMMARY)
        self.assert_renewal(FRENCH_TITLE)

    def test_language_patterns_are_not_specific_to_player_or_club(self):
        for title in ("Harry Kane agrees a new two-year deal with Bayern",
                      "Harry Kane has agreed a new 3-year contract at Bayern",
                      "Harry Kane signs new Bayern deal",
                      "Le Bayern a annoncé la prolongation de Harry Kane",
                      "Le Bayern a officialisé le renouvellement du contrat de Harry Kane",
                      "Le Bayern prolonge Harry Kane",
                      "Harry Kane a prolongé son contrat avec le Bayern"):
            with self.subTest(title=title):
                self.assert_renewal(title, player="Harry Kane", club="FC Bayern München")

    def test_clear_same_player_summary_can_remain_full_evidence(self):
        self.assert_renewal(SKY_TITLE, "Jude Bellingham has agreed a new contract at Real Madrid.", scope="full")

    def test_negative_or_contradictory_headline_or_summary_is_not_rescued(self):
        titles = ("Bellingham has not agreed a new five-year deal at Real Madrid",
                  "Bellingham never signs a new deal at Real Madrid",
                  "Le Real Madrid n'a pas bouclé la prolongation de Jude Bellingham",
                  "Le Real Madrid ne prolonge pas Jude Bellingham",
                  "Bellingham agrees new Real deal?",
                  "Le Real Madrid a bouclé la prolongation de Jude Bellingham ?")
        for title in titles:
            with self.subTest(title=title):
                self.assertIsNotNone(assess_transfer_evidence(title, BBC_SUMMARY, self.catalogues)["reason"])
        for summary in ("His agent denies agreeing a new contract.", "A new deal has not been agreed.",
                        "The contract extension was denied by the player.",
                        "La prolongation a été démentie par son agent.",
                        "Real Madrid did not confirm the deal.",
                        BBC_SUMMARY + " This is a charity match."):
            with self.subTest(summary=summary):
                self.assertIsNotNone(assess_transfer_evidence(SKY_TITLE, summary, self.catalogues)["reason"])

    def test_multiple_people_or_clubs_in_headline_remain_review(self):
        for title in ("Bellingham and Harry Kane agree new deals at Real Madrid",
                      "Bellingham agrees new deal at Real Madrid or Bayern",
                      "Bellingham agrees new deal at Real Madrid and an unnamed player signs",
                      "Le Real Madrid a bouclé la prolongation de Jude Bellingham et Harry Kane",
                      "Le Real Madrid et le Bayern ont bouclé la prolongation de Jude Bellingham",
                      "Sam Kane agrees new deal at Liverpool"):
            with self.subTest(title=title):
                self.assertIsNotNone(assess_transfer_evidence(title, BBC_SUMMARY, self.catalogues)["reason"])

    def test_non_contract_deals_and_unlinked_fragments_are_not_renewals(self):
        for title in ("Bellingham agrees new sponsorship deal at Real Madrid",
                      "Bellingham agrees new charity deal at Real Madrid",
                      "Bellingham agrees new five-year TV deal at Real Madrid",
                      "Bellingham: new deal, Real Madrid transfer rumours",
                      "Le Real Madrid a bouclé la prolongation du partenariat avec Jude Bellingham"):
            with self.subTest(title=title):
                self.assertIsNotNone(assess_transfer_evidence(title, catalogues=self.catalogues)["reason"])

    def test_colliding_player_alias_is_never_resolved_by_the_new_grammar(self):
        catalogues = build_entity_catalogues(players=[
            {"name": "Jude Bellingham", "aliases": ["Bellingham"]},
            {"name": "Jobe Bellingham", "aliases": ["Bellingham"]},
        ])
        result = assess_transfer_evidence(SKY_TITLE, catalogues=catalogues)
        self.assertIsNotNone(result["reason"])
        self.assertNotIn("player", result)


class RenewalScopePipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_roundup_and_historical_summary_never_reach_article_or_story(self):
        from pipeline_state import utcnow
        from speed_pipeline import SpeedPipeline
        from test_pipeline_repair import Database

        for title, summary, name, url in (
            (BBC_TITLE, BBC_SUMMARY, "BBC Sport", "https://www.bbc.co.uk/sport/football/articles/example"),
            (FRENCH_TITLE, FRENCH_SUMMARY, "Foot Mercato", "https://www.footmercato.net/example"),
        ):
            with self.subTest(source=name), patch.object(socket.socket, "connect", side_effect=AssertionError("No networking")):
                db = Database()
                pipeline = SpeedPipeline(db)
                pipeline._assign_article_image = AsyncMock()
                event = {"id": "renewal", "status": "pending", "created_at": utcnow(),
                         "headline_raw": title, "summary": summary, "body_raw": summary,
                         "source_name": name, "source_url": url, "source_published_at": utcnow()}
                await db.events.insert_one(event)
                result = await pipeline.process_pending_events(1)
                self.assertEqual(result["created_draft"], 1)
                article = await db.articles.find_one({})
                story = await db.transfer_stories.find_one({})
                stored = await db.events.find_one({"id": "renewal"})
                self.assertEqual((article["evidence_scope"], article["source_summary"], article["transfer_type"]),
                                 ("headline", "", "extension"))
                self.assertEqual(story["sources"][0]["raw_summary"], "")
                self.assertEqual(stored["body_raw"], summary)
                self.assertIsNone(article["from_club"])
                for excluded in ("Dortmund", "Kounde", "Schade", "Liverpool"):
                    self.assertNotIn(excluded, article["body"])


if __name__ == "__main__":
    unittest.main()
