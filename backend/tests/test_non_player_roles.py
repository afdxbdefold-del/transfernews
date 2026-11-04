"""Offline regression for the 4 November Nadal board-appointment incident."""
import os
import json
from pathlib import Path
import socket
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entity_catalogue import build_entity_catalogues
from pipeline_state import utcnow
from source_rewrite_checks import validate_source_rewrite
from speed_pipeline import GPTRewriter, SpeedPipeline
from test_pipeline_repair import Database
from transfer_evidence import assess_transfer_evidence, article_source_identity, source_player_candidates


TITLE = "Real Madrid : Rafael Nadal rejoint le conseil d’administration !"
SUMMARY = ("Rafale Nadal est un grand fan du Real Madrid. L’ancien tennisman, recordman du nombre "
           "de victoires à Roland-Garros (14 titres à Paris), va pouvoir assouvir sa passion "
           "de manière encore plus intense. (…)")
BAD_BODY = ("## Rafael Nadal pourrait entrer au conseil d’administration du Real Madrid\n\n"
            "Laut Foot Mercato könnte Rafael Nadal dem Vorstand von Real Madrid beitreten.")


class NonPlayerEvidenceTests(unittest.TestCase):
    def test_four_published_source_types_keep_their_verified_identities(self):
        # Public bodies and source events observed 4 November; scoped fields are
        # rebuilt using the normal evidence gate. No API, database or model call.
        path = Path(__file__).parent / "fixtures" / "verified_source_articles_20261104.json"
        for article in json.loads(path.read_text(encoding="utf-8")):
            with self.subTest(player=article["player_name"]):
                self.assertEqual(article_source_identity(article), (True, "OK"))
                self.assertEqual(validate_source_rewrite(article["body"], article), (True, "OK"))

    def test_summary_claim_with_full_name_support_from_headline_revalidates(self):
        catalogue = build_entity_catalogues(players=[{"name": "Morris Schröter"}])
        evidence = assess_transfer_evidence("Morris Schröter transfer latest",
            "Schröter unterschreibt beim FSV Zwickau. Trainer Mikel Arteta sprach über Arsenal.", catalogue)
        self.assertEqual([span["field"] for span in evidence["evidence_spans"]], ["summary", "headline"])
        article = {"source_headline": evidence["evidence_headline"], "source_summary": "",
                   "source_grounded": True, "evidence_scope": "claim", "evidence_spans": evidence["evidence_spans"],
                   "player_name": evidence["player"], "club_name": evidence["club"], "from_club": None,
                   "transfer_type": "permanent"}
        self.assertEqual(article_source_identity(article, catalogue), (True, "OK"))
        self.assertEqual(article_source_identity({**article, "source_headline": "forged"}, catalogue),
                         (False, "source_identity_unverified"))

    def test_exact_public_event_never_supplies_player_or_transfer_identity(self):
        self.assertEqual(source_player_candidates(TITLE, SUMMARY), [])
        self.assertEqual(assess_transfer_evidence(TITLE, SUMMARY), {"reason": "non_transfer_topic"})

    def test_non_player_role_works_without_tennis_word_and_with_a_known_player(self):
        for title in (
            "Rafael Nadal joins the board of directors at Real Madrid",
            "Rafael Nadal joins the board at Real Madrid",
            "Rafael Nadal rejoint le conseil d'administration du Real Madrid",
            "Rafael Nadal wechselt in den Vorstand von Real Madrid",
            "Rafael Nadal tritt dem Vorstand von Real Madrid bei",
            "Rafael Nadal entra en el consejo de administración del Real Madrid",
            "Rafael Nadal entra nella consiglio di amministrazione del Real Madrid",
            "Luka Modrić joins Real Madrid as a director",
            "Florian Wirtz rejoint Real Madrid comme entraîneur",
            "Florian Wirtz wechselt als neuer Trainer zu Real Madrid",
        ):
            with self.subTest(title=title):
                self.assertEqual(assess_transfer_evidence(title)["reason"], "non_transfer_topic")
                self.assertEqual(source_player_candidates(title), [])

    def test_tennis_variants_do_not_become_player_signings(self):
        for role in ("tennisman", "tenniswoman", "Tennisprofi", "tennisspieler", "tenista"):
            with self.subTest(role=role):
                self.assertEqual(assess_transfer_evidence(
                    "Rafael Nadal joins Real Madrid", f"Rafael Nadal is a former {role}.")["reason"],
                    "non_transfer_topic")

    def test_city_paris_never_means_psg_even_if_database_supplies_old_alias(self):
        catalogues = build_entity_catalogues(clubs=[{"name": "Paris Saint-Germain", "aliases": ["Paris"]},
                                                   {"name": "Paris FC"}])
        self.assertNotIn("paris", catalogues["clubs"])
        self.assertIsNotNone(assess_transfer_evidence("Florian Wirtz linked to Paris", catalogues=catalogues)["reason"])
        for club in ("PSG", "Paris Saint-Germain", "Paris FC"):
            with self.subTest(club=club):
                result = assess_transfer_evidence(f"Florian Wirtz linked to {club}", catalogues=catalogues)
                self.assertIsNone(result["reason"])
                self.assertEqual(result["club"], "Paris FC" if club == "Paris FC" else "Paris Saint-Germain")

    def test_director_announcing_a_real_transfer_is_not_a_role_change(self):
        result = assess_transfer_evidence(
            "Florian Wirtz joins Real Madrid", "The director announced the signing.")
        self.assertIsNone(result["reason"])
        self.assertEqual(result["club"], "Real Madrid")

    def test_manager_background_and_board_attribution_do_not_change_player_role(self):
        title = "Florian Wirtz joins Real Madrid"
        for summary in (
            "Carlo Ancelotti is in his first season as manager.",
            "Carlo Ancelotti arbeitet seit einem Jahr als Trainer.",
            "Der im Vorstand tätige Direktor bestätigte die Verpflichtung.",
            "The board of directors approved the signing.",
        ):
            with self.subTest(summary=summary):
                result = assess_transfer_evidence(title, summary)
                self.assertIsNone(result["reason"])
                self.assertEqual((result["player"], result["club"]), ("Florian Wirtz", "Real Madrid"))
                article = {"source_headline": title, "source_summary": summary, "source_name": "BBC Sport",
                           "source_grounded": True, "evidence_scope": "full", "transfer_type": "permanent",
                           "transfer_status": "official", "player_name": "Florian Wirtz", "club_name": "Real Madrid"}
                body = "## Florian Wirtz wechselt zu Real Madrid\nLaut BBC Sport wechselt Florian Wirtz zu Real Madrid. " + summary
                self.assertEqual(validate_source_rewrite(body, article), (True, "OK"))

    def test_final_guard_rechecks_false_old_identity_flags(self):
        article = {"source_headline": TITLE, "source_summary": SUMMARY, "source_grounded": True,
                   "evidence_scope": "full", "source_name": "Foot Mercato", "player_name": "Rafael Nadal",
                   "club_name": "Paris Saint-Germain", "from_club": "Real Madrid", "entity_confidence": 1.0,
                   "transfer_type": "permanent", "transfer_status": "rumor"}
        self.assertEqual(article_source_identity(article), (False, "source_identity_unverified"))
        self.assertEqual(validate_source_rewrite(BAD_BODY, article), (False, "source_identity_unverified"))

    def test_final_guard_requires_target_and_checks_recognizable_role_reversal(self):
        article = {"source_headline": "Florian Wirtz transfer from Bayern to Liverpool", "source_summary": "",
                   "source_grounded": True, "source_name": "BBC Sport", "evidence_scope": "headline",
                   "player_name": "Florian Wirtz", "club_name": "FC Liverpool", "from_club": "FC Bayern München",
                   "transfer_type": "permanent", "transfer_status": "rumor"}
        for change in ({"club_name": "FC Bayern München"}, {"player_name": "Harry Kane"}, {"from_club": "Real Madrid"}):
            self.assertEqual(article_source_identity({**article, **change}), (False, "source_identity_mismatch"))
        self.assertEqual(validate_source_rewrite("Laut BBC Sport könnte Florian Wirtz wechseln.", article),
                         (False, "missing_rewrite_identity"))
        self.assertEqual(validate_source_rewrite(
            "Laut BBC Sport könnte Florian Wirtz von Liverpool zu Bayern wechseln.", article),
            (False, "rewrite_identity_mismatch"))
        self.assertEqual(validate_source_rewrite(
            "## Florian Wirtz könnte zu Liverpool wechseln\n"
            "Laut BBC Sport könnte Florian Wirtz von Liverpool zu Bayern wechseln.", article),
            (False, "rewrite_identity_mismatch"))
        self.assertEqual(validate_source_rewrite(
            "Laut BBC Sport könnte Florian Wirtz von Bayern zu Liverpool wechseln.", article), (True, "OK"))
        self.assertEqual(validate_source_rewrite(
            "Laut BBC Sport könnte Florian Wirtz dem Vorstand von Liverpool beitreten.", article),
            (False, "non_player_rewrite"))


class NonPlayerPipelineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = Database()
        self.pipeline = SpeedPipeline(self.db)
        self.pipeline._assign_article_image = AsyncMock()
        for context in (patch.object(socket.socket, "connect", side_effect=AssertionError("No networking")),
                        patch.dict(os.environ, {"OPENAI_API_KEY": "offline-fixture"})):
            context.start()
            self.addCleanup(context.stop)

    async def test_exact_event_is_reviewed_before_story_article_or_image_write(self):
        event = {"id": "nadal-incident", "status": "pending", "created_at": utcnow(),
                 "headline_raw": TITLE, "body_raw": SUMMARY, "source_published_at": utcnow(),
                 "source_name": "Foot Mercato", "source_url": "https://www.footmercato.net/fixture"}
        await self.db.events.insert_one(event)
        result = await self.pipeline.process_pending_events(1)
        self.assertEqual(result["review"], 1)
        self.assertEqual(await self.db.articles.count_documents({}), 0)
        self.assertEqual(await self.db.transfer_stories.count_documents({}), 0)
        self.pipeline._assign_article_image.assert_not_called()

    async def test_old_incorrect_draft_is_held_before_any_model_request(self):
        await self.db.articles.insert_one({
            "id": "old-wrong-draft", "status": "draft", "needs_gpt_rewrite": True,
            "source_headline": TITLE, "source_summary": SUMMARY, "source_grounded": True,
            "evidence_scope": "full", "source_name": "Foot Mercato", "source_published_at": utcnow(),
            "player_name": "Rafael Nadal", "club_name": "Paris Saint-Germain", "from_club": "Real Madrid",
            "transfer_type": "permanent", "transfer_status": "rumor", "auto_publish_eligible": True,
            "content_revision": 1,
        })
        create = AsyncMock(side_effect=AssertionError("An invalid draft must not request a rewrite"))
        client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create)),
                                       close=AsyncMock())
        with patch("openai.AsyncOpenAI", return_value=client):
            self.assertFalse(await GPTRewriter(self.db).rewrite_article("old-wrong-draft"))
        create.assert_not_called()
        held = await self.db.articles.find_one({"id": "old-wrong-draft"})
        self.assertEqual((held["status"], held["rewrite_status"], held["rewrite_review_reason"]),
                         ("draft", "review", "source_identity_unverified"))
        self.assertNotIn("published_at", held)


if __name__ == "__main__":
    unittest.main()
