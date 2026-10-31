"""Source-exact relation coverage; no database, SDK or network calls."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entity_catalogue import build_entity_catalogues
from transfer_evidence import assess_transfer_evidence, unsupported_headline_detail


BILD_TITLE = "Transfer-Coup - Ost-Klub holt Aufstiegshelden zurück"
BILD_SUMMARY = "Morris Schröter unterschreibt beim FSV Zwickau bis 2028 und steht gegen Aue im Kader."
KICKER_TITLE = 'Neuzugang mit Stallgeruch: "Unterschiedsspieler" Schröter kehrt nach Zwickau zurück'
KICKER_SUMMARY = "Der FSV Zwickau hat sich noch einmal verstärkt. Morris Schröter kehrt nach sechs Jahren zurück in die Mulde."
KROUPI_TITLE = "Barcelone : la piste Eli Junior Kroupi relancée pour l’été"
KROUPI_SUMMARY = (
    "Le FC Barcelone n’a pas oublié Eli Junior Kroupi. Après avoir tenté de recruter l’attaquant français "
    "de Bournemouth lors du dernier mercato estival, le club catalan continuerait de surveiller (…) "
)


class SourceClaimEvidenceTests(unittest.TestCase):
    def assert_exact_claim(self, result, title, summary):
        self.assertEqual(result["evidence_scope"], "claim")
        self.assertEqual(result["evidence_summary"], "")
        originals = {"headline": title, "summary": summary}
        for span in result["evidence_spans"]:
            self.assertEqual(originals[span["field"]][span["start"]:span["end"]], span["text"])
        self.assertEqual(result["evidence_headline"], "\n".join(s["text"] for s in result["evidence_spans"]))

    def test_actual_bild_signing_uses_unknown_full_names_and_no_opponent_origin(self):
        catalogues = build_entity_catalogues()
        before = {key: dict(catalogues[key]) for key in ("players", "clubs")}
        result = assess_transfer_evidence(BILD_TITLE, BILD_SUMMARY, catalogues)
        self.assertEqual((result["player"], result["club"], result["from_club"], result["verified_stage"]),
                         ("Morris Schröter", "FSV Zwickau", None, "official"))
        self.assert_exact_claim(result, BILD_TITLE, BILD_SUMMARY)
        self.assertEqual(result["evidence_headline"], BILD_SUMMARY)
        self.assertEqual({key: catalogues[key] for key in before}, before)

    def test_kicker_same_return_has_same_complete_identity_without_invented_first_name(self):
        result = assess_transfer_evidence(KICKER_TITLE, KICKER_SUMMARY)
        self.assertEqual((result["player"], result["club"], result["from_club"]),
                         ("Morris Schröter", "FSV Zwickau", None))
        self.assertNotIn("2028", result.get("evidence_headline", KICKER_TITLE + KICKER_SUMMARY))
        self.assertIsNotNone(assess_transfer_evidence(KICKER_TITLE)["reason"])

    def test_actual_french_renewed_interest_is_isolated_from_old_attempt(self):
        result = assess_transfer_evidence(KROUPI_TITLE, KROUPI_SUMMARY)
        self.assertEqual((result["player"], result["club"], result["from_club"], result["verified_stage"]),
                         ("Eli Junior Kroupi", "FC Barcelona", None, "rumor"))
        self.assertNotEqual(result.get("transfer_type"), "extension")
        self.assert_exact_claim(result, KROUPI_TITLE, KROUPI_SUMMARY)
        self.assertEqual(result["evidence_headline"], KROUPI_TITLE)
        self.assertNotIn("Bournemouth", result["evidence_headline"])

    def test_denied_bid_cannot_be_replaced_by_a_market_teaser(self):
        teaser = ("Alors que JJ Gabriel, jeune attaquant de 16 ans appartenant à Manchester United, "
                  "fait actuellement beaucoup parler de lui sur le marché des transferts, "
                  "son nom a notamment été associé à plusieurs (…)")
        # Even a fully known player must not turn his employer into the buyer.
        catalogues = build_entity_catalogues(players=[{"name": "JJ Gabriel"}])
        for headline in (
            "Le PSG n’a formulé aucune offre pour JJ Gabriel !",
            "Le PSG n'a pas fait d'offre pour JJ Gabriel",
            "PSG : aucune offre pour JJ Gabriel",
        ):
            with self.subTest(headline=headline):
                self.assertEqual(assess_transfer_evidence(headline, teaser, catalogues),
                                 {"reason": "negated_transfer"})
        for affiliation in ("appartenant à", "appartient toujours à", "sous contrat à"):
            with self.subTest(affiliation=affiliation):
                result = assess_transfer_evidence("Le marché des transferts",
                                                  teaser.replace("appartenant à", affiliation), catalogues)
                self.assertIsNotNone(result["reason"])

    def test_affiliation_does_not_hide_a_separate_explicit_destination(self):
        title = "Liverpool surveille Florian Wirtz"
        result = assess_transfer_evidence(title, "Florian Wirtz appartient à Manchester United.")
        self.assertEqual((result["player"], result["club"]), ("Florian Wirtz", "FC Liverpool"))
        self.assert_exact_claim(result, title, "Florian Wirtz appartient à Manchester United.")

    def test_generic_full_names_and_clubs_need_no_catalogue_entry(self):
        for title, person, club in (
            ("Nico Neumann unterschreibt beim SC Hafenstadt", "Nico Neumann", "SC Hafenstadt"),
            ("João Ribeiro unterzeichnet einen Vertrag bei FC Neustadt", "João Ribeiro", "FC Neustadt"),
            ("Leeds United signs Florian Wirtz", "Florian Wirtz", "Leeds United"),
            ("Newtown United signs Sam Kane", "Sam Kane", "Newtown United"),
        ):
            with self.subTest(title=title):
                result = assess_transfer_evidence(title)
                self.assertIsNone(result["reason"])
                self.assertEqual((result["player"], result["club"]), (person, club))
                self.assertNotEqual(result["club"], "Manchester United")

    def test_publisher_and_historical_club_are_not_destinations(self):
        title = "According to The Athletic, Liverpool are interested in Florian Wirtz"
        summary = "He played for Bayer Leverkusen."
        result = assess_transfer_evidence(title, summary)
        self.assertEqual((result["player"], result["club"], result["from_club"]),
                         ("Florian Wirtz", "FC Liverpool", None))
        self.assert_exact_claim(result, title, summary)
        self.assertEqual(assess_transfer_evidence("Athletic Bilbao signs Florian Wirtz")["club"], "Athletic Bilbao")

    def test_complete_interest_clause_excludes_squad_building_coach_aside(self):
        title = "Arsenal track another forward"
        summary = ("Arsenal are reportedly monitoring Brighton & Hove Albion striker Charalampos Kostoulas "
                   "as Mikel Arteta looks to strengthen his attacking options.")
        catalogues = build_entity_catalogues(clubs=[{"name": "Brighton & Hove Albion"}])
        result = assess_transfer_evidence(title, summary, catalogues)
        self.assertEqual((result["player"], result["club"], result["verified_stage"]),
                         ("Charalampos Kostoulas", "FC Arsenal", "rumor"))
        self.assert_exact_claim(result, title, summary)
        self.assertNotIn("Mikel Arteta", result["evidence_headline"])

    def test_competing_targets_or_players_are_not_silently_dropped(self):
        cases = (
            ("Liverpool and Arsenal are interested in Florian Wirtz", ""),
            ("Liverpool are interested in Florian Wirtz", "Arsenal are interested in Florian Wirtz."),
            (BILD_TITLE, BILD_SUMMARY + " João Silva joins Liverpool."),
            ("Liverpool signs João Silva and Carlos Pinto", ""),
            (KROUPI_TITLE, "Arsenal are interested in Eli Junior Kroupi."),
            ("Arsenal track another forward", "Arsenal are reportedly monitoring Florian Wirtz "
             "as Mikel Arteta looks to strengthen his squad by signing João Silva."),
            (BILD_TITLE, "Morris Schröter unterschreibt beim FSV Zwickau. "
             "Der FSV Zwickau gibt Morris Schröter an den SC Hafenstadt ab."),
            (BILD_TITLE, "Morris Schröter unterschreibt beim FSV Zwickau. João Silva wird ebenfalls verpflichtet."),
        )
        for title, summary in cases:
            with self.subTest(title=title, summary=summary):
                self.assertIsNotNone(assess_transfer_evidence(title, summary)["reason"])

    def test_negation_hypothesis_question_and_other_sports_remain_review(self):
        for title, summary in (
            ("Nico Neumann unterschreibt nicht beim SC Hafenstadt", ""),
            ("Nico Neumann unterschreibt beim SC Hafenstadt, wenn der Test gelingt", ""),
            ("Falls Nico Neumann unterschreibt beim SC Hafenstadt", ""),
            ("Nico Neumann unterschreibt beim SC Hafenstadt?", ""),
            ("Barcelone : la piste Eli Junior Kroupi relancée?", ""),
            ("Transfer-Coup im Handball", BILD_SUMMARY),
            (BILD_TITLE, BILD_SUMMARY + " The charity event raises money."),
            ("Injury update on Morris Schröter", BILD_SUMMARY),
            ("Transfer-Coup", "Nico Neumann unterschreibt beim SC Hafenstadt doch nicht."),
            ("Transfer-Coup", "Nico Neumann unterschreibt beim SC Hafenstadt erst morgen."),
            ("Transfer-Coup", "Nico Neumann unterschreibt beim SC Hafenstadt als Trainer."),
            (BILD_TITLE, "Morris Schröter unterschreibt beim FSV Zwickau. Der Verein dementiert die Meldung."),
            ("Neuzugang: Nico Neumann kehrt nach SC Hafenstadt zurück", "Der Verein dementiert die Meldung."),
            ("Neuzugang: Nico Neumann kehrt nach SC Hafenstadt zurück, wenn der Test gelingt.", ""),
            ("Neuzugang: Nico Neumann kehrt nach SC Hafenstadt zurück, aber doch nicht.", ""),
            ("Neuzugang: Nico Neumann kehrt nach SC Hafenstadt zurück, erst morgen.", ""),
        ):
            with self.subTest(title=title, summary=summary):
                self.assertIsNotNone(assess_transfer_evidence(title, summary)["reason"])

    def test_actual_disciplinary_fine_is_not_a_current_alvarez_transfer(self):
        title = "Irrisoria multa de la RFEF al Barça por el 'caso Julián Álvarez'"
        summary = ("Ya hay resolución al 'caso Julián Álvarez' y al expediente extraordinario abierto a finales "
                   "de julio a raíz de la denuncia presentada por el Atlético de Madrid contra el FC Barcelona "
                   "a la RFEF por supuestamente 'tocar' a un jugador con contrato en vigor. El expediente no pudo "
                   "ser abierto por la FIFA porque, como ya explicamos, no tiene competencias en este caso. "
                   "El Barça sólo deberá pagar 602 euros.")
        self.assertEqual(assess_transfer_evidence(title, summary)["reason"], "non_transfer_topic")

    def test_competing_headline_target_is_not_hidden_by_one_summary_clause(self):
        title = "Everton face Tottenham competition in race for 22-year-old La Liga goalscorer"
        summary = ("Everton are reportedly interested in signing Real Sociedad striker Orri Oskarsson "
                   "as David Moyes looks to strengthen his attacking options ahead of the January transfer window.")
        catalogues = build_entity_catalogues(clubs=[{"name": "Everton"}, {"name": "Real Sociedad"}])
        self.assertEqual(assess_transfer_evidence(title, summary, catalogues)["reason"], "ambiguous_transfer_direction")

    def test_rewrite_cannot_replace_source_club_with_known_suffix_or_other_unknown_club(self):
        self.assertIsNotNone(unsupported_headline_detail(
            "Manchester United verpflichtet Florian Wirtz.", "Leeds United signs Florian Wirtz"))
        self.assertIsNotNone(unsupported_headline_detail(
            "Nico Neumann unterschreibt beim FC Neustadt.", "Nico Neumann unterschreibt beim SC Hafenstadt"))


class SourceClaimPipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_source_fixtures_pass_real_gate_and_checked_rewrite_offline(self):
        import os
        import socket
        import types
        from unittest.mock import AsyncMock, patch
        from test_pipeline_repair import Database
        from pipeline_state import utcnow
        from speed_pipeline import SpeedPipeline, GPTRewriter

        cases = (
            ("BILD", BILD_TITLE, BILD_SUMMARY, "Morris Schröter", "FSV Zwickau",
             "## Morris Schröter unterschreibt beim FSV Zwickau\n\n"
             "Laut BILD hat Morris Schröter beim FSV Zwickau einen Vertrag bis 2028 unterschrieben."),
            ("Foot Mercato", KROUPI_TITLE, KROUPI_SUMMARY, "Eli Junior Kroupi", "FC Barcelona",
             "## FC Barcelona soll wieder Interesse an Eli Junior Kroupi haben\n\n"
             "Laut Foot Mercato soll der FC Barcelona wieder an Eli Junior Kroupi interessiert sein."),
        )
        for source, title, summary, player, club, rewrite in cases:
            with self.subTest(source=source):
                db = Database()
                pipeline = SpeedPipeline(db)
                pipeline._assign_article_image = AsyncMock()
                event = {"id": source, "status": "pending", "created_at": utcnow(),
                         "source_published_at": utcnow(), "headline_raw": title, "body_raw": summary,
                         "source_name": source, "source_url": ("https://www.bild.de/exact-fixture" if source == "BILD"
                                                                else "https://www.footmercato.net/exact-fixture")}
                await db.events.insert_one(event)
                client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(
                    create=AsyncMock(return_value=types.SimpleNamespace(
                        usage=types.SimpleNamespace(total_tokens=100), choices=[types.SimpleNamespace(
                            message=types.SimpleNamespace(content=rewrite))])))), close=AsyncMock())
                with patch.object(socket.socket, "connect", side_effect=AssertionError("Network disabled")), \
                        patch.dict(os.environ, {"OPENAI_API_KEY": "offline-fixture"}), \
                        patch("openai.AsyncOpenAI", return_value=client):
                    processed = await pipeline.process_pending_events(1)
                    self.assertEqual(processed["created_draft"], 1)
                    draft = await db.articles.find_one({})
                    self.assertIn(player, draft["title"])
                    self.assertIn(club, draft["title"])
                    self.assertEqual(draft["evidence_scope"], "claim")
                    self.assertEqual(draft["source_summary"], "")
                    completed = await GPTRewriter(db).process_rewrite_queue(1)
                self.assertEqual(completed["published"], 1, (completed, await db.articles.find_one({})))
                self.assertEqual((await db.articles.find_one({}))["body"], rewrite)
                self.assertEqual((await db.events.find_one({}))["body_raw"], summary)
                self.assertEqual(client.chat.completions.create.await_count, 1)


if __name__ == "__main__":
    unittest.main()
