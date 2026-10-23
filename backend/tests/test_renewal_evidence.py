"""Actual October RSS claims and conservative renewal counterexamples; offline."""
from pathlib import Path
import os
import socket
import sys
import types
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
FRENCH_TOPIC_TITLE = "Real Madrid : Arda Güler a prolongé"
FRENCH_TOPIC_SUMMARY = (
    "Au Real Madrid depuis l’été 2023, Arda Güler va continuer l’aventure merengue. "
    "Selon les informations du journaliste italien Fabrizio Romano, le milieu offensif turc "
    "a signé son nouveau contrat avec (…)"
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

    def test_actual_french_topic_renewal_retains_same_player_summary(self):
        self.assert_renewal(FRENCH_TOPIC_TITLE, player="Arda Güler")
        self.assert_renewal(FRENCH_TOPIC_TITLE, FRENCH_TOPIC_SUMMARY,
                           player="Arda Güler", scope="full")
        self.assert_renewal("Bayern: Harry Kane a prolongé.",
                           player="Harry Kane", club="FC Bayern München")

    def test_french_topic_renewal_is_only_a_complete_affirmative_claim(self):
        for title in (
            "Real Madrid : Arda Güler n’a pas prolongé",
            "Real Madrid : Arda Güler a prolongé ?",
            "Real Madrid : Arda Güler aurait prolongé",
            "Real Madrid : Arda Güler pourrait prolonger",
            "Real Madrid : si Arda Güler a prolongé",
            "Real Madrid : Arda Güler a prolongé ses vacances",
            "Real Madrid : Arda Güler a prolongé son séjour",
            "Real Madrid : Arda Güler et Jude Bellingham ont prolongé",
            "Real Madrid : Arda Güler a prolongé et Harry Kane aussi",
            "Real Madrid : Arda Güler a prolongé avec le Bayern",
            "Real Madrid et Bayern : Arda Güler a prolongé",
        ):
            for summary in ("", FRENCH_TOPIC_SUMMARY):
                with self.subTest(title=title, with_summary=bool(summary)):
                    self.assertIsNotNone(assess_transfer_evidence(
                        title, summary, self.catalogues)["reason"])

    def test_french_topic_renewal_preserves_negation_and_topic_guards(self):
        for summary in ("La prolongation a été démentie par son agent.",
                        "Arda Güler n’a pas signé de nouveau contrat.",
                        "Arda Güler has agreed to a charity appearance."):
            with self.subTest(summary=summary):
                self.assertIsNotNone(assess_transfer_evidence(
                    FRENCH_TOPIC_TITLE, summary, self.catalogues)["reason"])

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
    async def test_french_topic_existing_review_reprocesses_same_draft_then_validated_publication(self):
        from pipeline_state import utcnow
        from publication_policy import PIPELINE_VERSION
        from speed_pipeline import GPTRewriter, SpeedPipeline
        from test_pipeline_repair import Database

        rewrite = (
            "## Arda Güler soll seinen Vertrag bei Real Madrid verlängert haben\n\n"
            "Laut Foot Mercato soll der türkische offensive Mittelfeldspieler Arda Güler "
            "seinen Vertrag bei Real Madrid verlängert haben. "
            "Das Portal beruft sich dabei auf Informationen des italienischen Journalisten Fabrizio Romano. "
            "Güler spielt dem Bericht zufolge seit dem Sommer 2023 bei Real Madrid."
        )
        complete = AsyncMock(return_value=types.SimpleNamespace(
            id="offline-response", usage=types.SimpleNamespace(total_tokens=123),
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=rewrite))]))
        client = types.SimpleNamespace(
            chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=complete)), close=AsyncMock())
        with patch.object(socket.socket, "connect", side_effect=AssertionError("No networking")), \
                patch.dict(os.environ, {"OPENAI_API_KEY": "offline-test"}):
            db = Database()
            pipeline = SpeedPipeline(db)
            pipeline._assign_article_image = AsyncMock()
            await db.events.insert_one({
                "id": "french-topic-renewal", "status": "review", "created_at": utcnow(),
                "review_reason": "ambiguous_transfer_direction", "pipeline_version": "previous-policy",
                "headline_raw": FRENCH_TOPIC_TITLE, "summary": FRENCH_TOPIC_SUMMARY,
                "body_raw": FRENCH_TOPIC_SUMMARY, "source_name": "Foot Mercato",
                "source_url": "https://www.footmercato.net/a3045578490507207433-real-madrid-arda-guler-a-prolonge",
                "source_published_at": utcnow(),
            })
            result = await pipeline.process_pending_events(1)
            self.assertEqual(result["created_draft"], 1)
            draft = await db.articles.find_one({})
            self.assertEqual((draft["status"], draft["transfer_type"], draft["from_club"]),
                             ("draft", "extension", None))
            self.assertIn("Vertragsverlängerung", draft["title"])
            self.assertEqual((draft["source_headline"], draft["source_summary"], draft["evidence_scope"]),
                             (FRENCH_TOPIC_TITLE, FRENCH_TOPIC_SUMMARY, "full"))
            self.assertTrue(draft["auto_publish_eligible"])
            self.assertIsNone(draft["published_at"])
            self.assertFalse(GPTRewriter(db).validate_rewrite(
                FRENCH_TOPIC_SUMMARY, rewrite.replace("2023", "2031"),
                evidence=FRENCH_TOPIC_TITLE + "\n" + FRENCH_TOPIC_SUMMARY,
                evidence_scope="source")[0])
            # Existing live shape: same source was already processed by v8 and
            # its generated body was held by the old translation detail guard.
            await db.events.update_one({"id": "french-topic-renewal"}, {"$set": {
                "pipeline_version": "20261023_source_grounded_v8"}})
            await db.articles.update_one({"id": draft["id"]}, {"$set": {
                "publication_policy_version": "20261023_source_grounded_v8",
                "rewrite_status": "review", "rewrite_failed": True, "needs_gpt_rewrite": False,
                "rewrite_review_reason": "Unbelegte biografische Angabe in Überschriftenmeldung: Mittelfeldspieler"}})
            reconsidered = await pipeline.process_pending_events(1)
            self.assertEqual((reconsidered["updated"], reconsidered["created_draft"]), (1, 0))
            pending = await db.articles.find_one({"id": draft["id"]})
            self.assertEqual((pending["status"], pending["rewrite_status"], pending["needs_gpt_rewrite"]),
                             ("draft", "pending", True))
            self.assertEqual(pending["content_revision"], draft["content_revision"] + 1)
            self.assertEqual(len(await db.articles.find({}).to_list(10)), 1)
            self.assertEqual(len(await db.transfer_stories.find({}).to_list(10)), 1)
            with patch("openai.AsyncOpenAI", return_value=client):
                result = await GPTRewriter(db).process_rewrite_queue(1)
            self.assertEqual((result["rewritten"], result["published"]), (1, 1))
            complete.assert_awaited_once()
            saved = await db.articles.find_one({})
            self.assertEqual((saved["status"], saved["body"], saved["rewrite_status"]),
                             ("published", rewrite, "complete"))
            self.assertEqual(saved["rewrite_completed_revision"], saved["content_revision"])
            self.assertFalse(saved["has_researched_context"])
            event = await db.events.find_one({"id": "french-topic-renewal"})
            self.assertEqual((event["pipeline_version"], event["body_raw"]),
                             (PIPELINE_VERSION, FRENCH_TOPIC_SUMMARY))
            self.assertEqual((await pipeline.process_pending_events(1))["processed"], 0)

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
