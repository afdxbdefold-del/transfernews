"""Offline evidence coverage tests: catalogue collisions and actual RSS claims."""
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entity_catalogue import build_entity_catalogues, load_entity_catalogues
from transfer_evidence import assess_transfer_evidence, source_player_candidates, unsupported_headline_detail


BERNAL_TITLE = "La cláusula que tendrá Bernal en su nuevo contrato"
BERNAL_SUMMARY = (
    "El futuro de Marc Bernal en el Barça tiene fecha. El centrocampista azulgrana está a punto de ampliar "
    "su contrato con el club azulgrana hasta 2031. El mediocentro, convocado por la selección española sub-21 "
    "en este parón internacional, ampliará su vinculación contractual un par de temporadas más, hasta 2031. "
    "El propio director deportivo anunció el inminente acuerdo en la última asamblea."
)


class CatalogueTests(unittest.IsolatedAsyncioTestCase):
    async def test_loads_only_names_without_using_club_history(self):
        players = [{"name": "Nico Neumann", "full_name": "Nico Neumann", "short_name": "N. Neumann",
                    "aliases": ["Neumann"], "current_club_name": "Real Madrid"}]
        clubs = [{"name": "FC Teststadt", "short_name": "Teststadt", "aliases": ["Teststadt FC"]}]
        db = types.SimpleNamespace(**{
            name: types.SimpleNamespace(find=Mock(return_value=types.SimpleNamespace(to_list=AsyncMock(return_value=data))))
            for name, data in [("players", players), ("clubs", clubs)]
        })
        catalogues = await load_entity_catalogues(db)
        for collection in (db.players, db.clubs):
            query, projection = collection.find.call_args.args
            self.assertEqual(query, {})
            self.assertEqual(set(projection), {"_id", "name", "full_name", "short_name", "aliases"})
        result = assess_transfer_evidence("Teststadt signs Neumann", catalogues=catalogues)
        self.assertEqual((result["player"], result["club"], result["from_club"]),
                         ("Nico Neumann", "FC Teststadt", None))
        self.assertEqual(assess_transfer_evidence("Florian Wirtz joins Liverpool", catalogues=catalogues)["club"], "FC Liverpool")
        self.assertEqual(catalogues["players"]["n. neumann"], {"name": "Nico Neumann"})

    async def test_read_failure_propagates_instead_of_silent_loss_of_entities(self):
        collection = types.SimpleNamespace(find=Mock(return_value=types.SimpleNamespace(
            to_list=AsyncMock(side_effect=RuntimeError("offline database failure")))))
        with self.assertRaises(RuntimeError):
            await load_entity_catalogues(types.SimpleNamespace(players=collection, clubs=collection))

    def test_shared_alias_is_not_assigned_by_record_order(self):
        records = [{"name": "João Silva", "aliases": ["Silva"]}, {"name": "Rui Silva", "aliases": ["Silva"]}]
        for ordered in (records, list(reversed(records))):
            catalogues = build_entity_catalogues(ordered)
            self.assertNotIn("silva", catalogues["players"])
            self.assertIn("silva", catalogues["ambiguous_players"])
            self.assertEqual(assess_transfer_evidence("Liverpool signs Silva", catalogues=catalogues)["reason"], "ambiguous_players")
            self.assertEqual(assess_transfer_evidence("Liverpool signs João Silva", catalogues=catalogues)["player"], "João Silva")

    def test_shared_club_alias_is_reviewed_and_exact_static_identity_is_preserved(self):
        catalogues = build_entity_catalogues(clubs=[
            {"name": "Liverpool", "aliases": ["LFC"]},
            {"name": "Newtown Athletic", "aliases": ["Athletic Town"]},
            {"name": "Newtown City", "aliases": ["Athletic Town"]},
        ])
        self.assertEqual(assess_transfer_evidence("Florian Wirtz joins LFC", catalogues=catalogues)["club"], "FC Liverpool")
        self.assertEqual(assess_transfer_evidence("Florian Wirtz joins Athletic Town", catalogues=catalogues)["reason"], "ambiguous_clubs")

    def test_club_alias_inside_full_player_name_does_not_invent_origin(self):
        catalogues = build_entity_catalogues(players=[{"name": "André Santos"}], clubs=[{"name": "Santos"}])
        result = assess_transfer_evidence("Liverpool signs André Santos", catalogues=catalogues)
        self.assertEqual((result["player"], result["club"], result["from_club"]), ("André Santos", "FC Liverpool", None))


class SourceNameAndRelationTests(unittest.TestCase):
    def test_actual_bernal_renewal_uses_source_present_full_name_without_persistence(self):
        catalogues = build_entity_catalogues()
        before = dict(catalogues["players"])
        self.assertEqual(source_player_candidates(BERNAL_TITLE, BERNAL_SUMMARY, catalogues), ["Marc Bernal"])
        result = assess_transfer_evidence(BERNAL_TITLE, BERNAL_SUMMARY, catalogues)
        self.assertEqual((result["player"], result["club"], result["transfer_type"], result["evidence_scope"]),
                         ("Marc Bernal", "FC Barcelona", "extension", "full"))
        self.assertEqual(catalogues["players"], before)
        self.assertEqual(assess_transfer_evidence("Bernal renews contract at Barcelona")["reason"], "unresolved_entities")

    def test_unknown_full_player_name_in_explicit_transfer_claim(self):
        result = assess_transfer_evidence("Liverpool signs João Silva")
        self.assertEqual((result["player"], result["club"]), ("João Silva", "FC Liverpool"))
        self.assertEqual(assess_transfer_evidence("João Silva joins Liverpool")["player"], "João Silva")
        self.assertEqual(assess_transfer_evidence("Liverpool signs Silva")["reason"], "unresolved_entities")

    def test_unknown_full_name_is_not_the_known_player_with_the_same_surname(self):
        for name in ("Sam Kane", "Daniel Wirtz"):
            with self.subTest(name=name):
                self.assertEqual(assess_transfer_evidence(f"Liverpool signs {name}")["player"], name)
        self.assertEqual(assess_transfer_evidence("Liverpool signs Sam Kane and Harry Kane")["reason"], "ambiguous_players")
        self.assertIsNotNone(unsupported_headline_detail("Harry Kane joins Liverpool", "Liverpool signs Sam Kane"))

    def test_unknown_second_player_is_not_hidden_by_static_catalogue(self):
        for title in ("Liverpool signs João Silva and Carlos Pinto",
                      "Liverpool interested in Florian Wirtz and João Silva",
                      "Liverpool signs Florian Wirtz. João Silva joins Arsenal"):
            with self.subTest(title=title):
                self.assertEqual(assess_transfer_evidence(title)["reason"], "ambiguous_players")
        mixed = BERNAL_SUMMARY + " João Silva joins Liverpool."
        self.assertEqual(assess_transfer_evidence(BERNAL_TITLE, mixed)["reason"], "ambiguous_players")
        self.assertEqual(assess_transfer_evidence("Liverpool signs João Silva", "Carlos Pinto joins Arsenal")["reason"], "ambiguous_players")

    def test_capitalized_headline_phrases_clubs_and_staff_are_not_players(self):
        for title in ("Liverpool signs New Deal", "Transfer News joins Liverpool",
                      "Liverpool signs John Smith as new coach", "Liverpool signs The Future",
                      "Liverpool signs Unknown Star"):
            with self.subTest(title=title):
                self.assertIsNotNone(assess_transfer_evidence(title)["reason"])
                self.assertEqual(source_player_candidates(title), [])
        reported = "Liverpool interested in Florian Wirtz according to David Ornstein"
        self.assertEqual(source_player_candidates(reported), [])
        self.assertEqual(assess_transfer_evidence(reported)["player"], "Florian Wirtz")

    def test_common_explicit_interest_forms_preserve_direction(self):
        cases = ["Liverpool are monitoring Florian Wirtz", "Liverpool is eyeing Florian Wirtz",
                 "Liverpool keen to sign Florian Wirtz", "Liverpool beobachtet Florian Wirtz",
                 "Liverpool hat Florian Wirtz im Visier", "Liverpool will Florian Wirtz verpflichten",
                 "Liverpool ist an Florian Wirtz interessiert",
                 "Liverpool sigue de cerca Florian Wirtz", "Liverpool quiere fichar a Florian Wirtz",
                 "Liverpool surveille Florian Wirtz", "Liverpool veut recruter Florian Wirtz"]
        for title in cases:
            with self.subTest(title=title):
                self.assertEqual(assess_transfer_evidence(title)["club"], "FC Liverpool")
        result = assess_transfer_evidence("Liverpool monitoring Florian Wirtz from Bayern")
        self.assertEqual((result["club"], result["from_club"]), ("FC Liverpool", "FC Bayern München"))
        self.assertEqual(assess_transfer_evidence("Liverpool monitoring Florian Wirtz and Bayern")["reason"], "ambiguous_transfer_direction")

    def test_negation_charity_and_multi_entity_safeguards_remain(self):
        for title in ("Liverpool are not monitoring Florian Wirtz", "Liverpool nicht interessiert an Florian Wirtz",
                      "Marc Bernal no renovará su contrato con Barcelona", "Florian Wirtz ne prolonge pas son contrat à Liverpool"):
            with self.subTest(title=title):
                self.assertEqual(assess_transfer_evidence(title)["reason"], "negated_transfer")
        self.assertEqual(assess_transfer_evidence("Liverpool signs João Silva for a charity match")["reason"], "non_transfer_topic")
        self.assertEqual(assess_transfer_evidence("João Silva injury: Liverpool medical update")["reason"], "non_transfer_topic")

    def test_common_surname_homographs_do_not_create_a_second_player(self):
        result = assess_transfer_evidence("Florian Wirtz prolonge son contrat à Liverpool")
        self.assertEqual((result["player"], result["club"], result["transfer_type"]),
                         ("Florian Wirtz", "FC Liverpool", "extension"))
        self.assertEqual(assess_transfer_evidence("Son joins Liverpool")["player"], "Heung-Min Son")
        self.assertEqual(assess_transfer_evidence("Liverpool can sign Florian Wirtz")["reason"], "missing_transfer_context")

    def test_dynamic_and_unknown_extra_rewrite_entities_are_rejected(self):
        catalogues = build_entity_catalogues(players=[{"name": "Nico Neumann"}], clubs=[{"name": "FC Teststadt"}])
        source = "Liverpool signs Nico Neumann"
        self.assertIsNone(unsupported_headline_detail("Nico Neumann joins Liverpool", source, catalogues))
        self.assertIsNotNone(unsupported_headline_detail("Nico Neumann joins Liverpool from FC Teststadt", source, catalogues))
        self.assertIsNotNone(unsupported_headline_detail("Liverpool signs Nico Neumann and João Silva", source, catalogues))
        catalogues = build_entity_catalogues(players=[{"name": "André Santos"}], clubs=[{"name": "Santos"}])
        self.assertIsNotNone(unsupported_headline_detail("André Santos joins Liverpool from Santos",
                                                        "Liverpool signs André Santos", catalogues))

    def test_supported_spanish_midfield_position_translates_without_new_facts(self):
        rewrite = "Mundo Deportivo berichtet über eine mögliche Vertragsverlängerung von Mittelfeldspieler Marc Bernal beim FC Barcelona."
        self.assertIsNone(unsupported_headline_detail(rewrite, BERNAL_TITLE + "\n" + BERNAL_SUMMARY))
        for position in ("centrocampista", "mediocentro", "mediocampista", "milieu de terrain"):
            with self.subTest(position=position):
                evidence = f"Marc Bernal es {position} y ampliará su contrato con Barcelona."
                self.assertIsNone(unsupported_headline_detail(rewrite, evidence))
        no_position = "Marc Bernal ampliará su contrato con Barcelona hasta 2031."
        reason = unsupported_headline_detail(rewrite, no_position)
        self.assertIn("Unbelegte", reason)
        self.assertIn("Mittelfeldspieler", reason)

    def test_spanish_selection_is_not_evidence_of_nationality(self):
        evidence = BERNAL_TITLE + "\n" + BERNAL_SUMMARY
        for nationality in ("spanische", "brasilianische", "deutsche"):
            with self.subTest(nationality=nationality):
                reason = unsupported_headline_detail(
                    f"Der {nationality} Mittelfeldspieler Marc Bernal könnte seinen Vertrag bei Barcelona verlängern.", evidence)
                self.assertIn(nationality, reason)
        self.assertIsNone(unsupported_headline_detail("Marc Bernal ist spanischer Mittelfeldspieler und verlängert seinen Vertrag bei Barcelona.",
            "Marc Bernal es centrocampista de nacionalidad española y renueva su contrato con Barcelona."))
        self.assertIsNotNone(unsupported_headline_detail("Marc Bernal ist brasilianischer Mittelfeldspieler und verlängert seinen Vertrag bei Barcelona.",
            "Marc Bernal es centrocampista de nacionalidad española y renueva su contrato con Barcelona."))


if __name__ == "__main__":
    unittest.main()
