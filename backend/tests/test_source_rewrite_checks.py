import pytest

from source_rewrite_checks import validate_source_rewrite


BBC = {
    "source_name": "BBC Sport",
    "source_headline": "Arsenal may move for Endrick in January - Sunday's gossip",
    "source_summary": "Mixed roundup: other players have signed for other clubs.",
    "evidence_scope": "headline", "transfer_status": "rumor", "transfer_type": "permanent",
}


def test_accepts_compact_attributed_rumour_without_converting_probability_to_fact():
    rewrite = ("## Endrick im Gespräch\nLaut BBC Sport könnte Arsenal im Januar einen Vorstoß für Endrick erwägen. "
               "Ein Wechsel ist noch nicht bestätigt.")
    assert validate_source_rewrite(rewrite, BBC) == (True, "OK")


@pytest.mark.parametrize("rewrite", [
    "Laut BBC Sport ist der Wechsel von Endrick zu Arsenal offiziell bestätigt. Der Vertrag wurde unterschrieben.",
    "Laut BBC Sport könnte Arsenal interessiert sein. Der Transfer ist abgeschlossen.",
    "Laut BBC Sport könnte Arsenal interessiert sein, aber Endrick wechselt zu Arsenal.",
    "BBC Sport berichtet: Endrick wechselt zu Arsenal. Es gibt keinen Zweifel.",
    "Laut BBC Sport ist der Wechsel kein Gerücht mehr.",
    "Laut BBC Sport hat Endrick ohne Zögern bei Arsenal unterschrieben. Zuvor war der Wechsel ein Gerücht.",
    "Laut BBC Sport hat Endrick ohne Zweifel bei Arsenal unterschrieben. Zuvor war der Wechsel ein Gerücht.",
    "Laut BBC Sport könnte Arsenal interessiert sein. Arsenal hat Endrick unter Vertrag genommen.",
    "Laut BBC Sport könnte Arsenal interessiert sein. Arsenal nimmt Endrick unter Vertrag.",
])
def test_rejects_actual_certainty_escalation_even_when_a_modal_appears_elsewhere(rewrite):
    assert validate_source_rewrite(rewrite, BBC) == (False, "unsupported_completion_claim")


@pytest.mark.parametrize("rewrite", [
    "Endrick könnte im Januar zu Arsenal wechseln.",
    "Laut einer Quelle könnte Endrick zu Arsenal wechseln.",
    "BBC Sport ist eine Sportredaktion. Endrick könnte zu Arsenal wechseln.",
])
def test_requires_attribution_to_the_named_publisher(rewrite):
    assert validate_source_rewrite(rewrite, BBC) == (False, "missing_named_source_attribution")


def test_publisher_punctuation_and_diacritics_do_not_break_attribution():
    article = {**BBC, "source_name": "L’Équipe"}
    assert validate_source_rewrite("L'Equipe berichtet, dass Endrick zu Arsenal wechseln könnte.", article)[0]


@pytest.mark.parametrize("rewrite", [
    "Laut BBC Sport wechselt Endrick möglicherweise zu Arsenal.",
    "Nach Informationen von BBC Sport könnte Endrick zu Arsenal wechseln.",
    "Laut BBC Sport könnte Endrick wechseln. Der Transfer ist nicht offiziell bestätigt.",
])
def test_normal_german_attribution_and_modal_word_order_remain_accepted(rewrite):
    assert validate_source_rewrite(rewrite, BBC)[0]


@pytest.mark.parametrize("stage,rewrite", [
    ("advanced", "Laut BBC Sport verhandelt Arsenal über einen Transfer von Endrick. Die Gespräche laufen."),
    ("near_done", "BBC Sport berichtet: Endrick steht kurz vor einem Wechsel zu Arsenal. Eine Unterschrift steht noch aus."),
])
def test_preserves_in_progress_stages(stage, rewrite):
    assert validate_source_rewrite(rewrite, {**BBC, "transfer_status": stage})[0]


def test_stage_label_and_old_generated_body_cannot_authorize_a_completed_transfer():
    article = {**BBC, "transfer_status": "official", "body": "Arsenal announced the completed signing of Endrick."}
    assert validate_source_rewrite("Laut BBC Sport hat Endrick bei Arsenal unterschrieben.", article) == (False, "unsupported_completion_claim")


def test_explicit_source_confirmation_accepts_completion():
    article = {**BBC, "transfer_status": "official", "source_headline": "Arsenal has signed Endrick"}
    assert validate_source_rewrite("Laut BBC Sport hat Endrick bei Arsenal unterschrieben.", article)[0]


def test_renewal_cannot_become_a_new_club_transfer():
    article = {**BBC, "source_name": "Mundo Deportivo", "source_headline": "Marc Bernal renueva con el Barcelona",
               "source_summary": "", "evidence_scope": "full", "transfer_type": "extension"}
    assert validate_source_rewrite("Laut Mundo Deportivo ist eine Vertragsverlängerung von Marc Bernal bei Barcelona im Gespräch.", article)[0]
    assert validate_source_rewrite("Laut Mundo Deportivo könnte Marc Bernal zum FC Barcelona wechseln.", article) == (False, "renewal_changed_to_transfer")


def test_renewal_from_summary_is_also_protected_but_headline_scope_ignores_mixed_summary():
    article = {**BBC, "source_summary": "The clubs discussed a contract renewal.", "evidence_scope": "full"}
    rewrite = "Laut BBC Sport könnte Endrick zu Arsenal wechseln."
    assert validate_source_rewrite(rewrite, article) == (False, "renewal_changed_to_transfer")
    assert validate_source_rewrite(rewrite, {**article, "evidence_scope": "headline"})[0]


def test_confirmed_spanish_renewal_accepts_a_german_renewal_not_a_move():
    article = {**BBC, "source_name": "Mundo Deportivo", "source_headline": "Marc Bernal renueva con el Barcelona",
               "source_summary": "", "transfer_status": "official", "transfer_type": "extension"}
    assert validate_source_rewrite("Laut Mundo Deportivo hat Marc Bernal seinen Vertrag bei Barcelona verlängert.", article)[0]
    assert validate_source_rewrite("Laut Mundo Deportivo wechselt Marc Bernal zum FC Barcelona.", article)[1] == "renewal_changed_to_transfer"


def test_loan_must_remain_a_loan_and_not_a_permanent_purchase():
    article = {**BBC, "source_headline": "Arsenal interested in Endrick loan", "source_summary": "", "transfer_type": "loan"}
    assert validate_source_rewrite("Laut BBC Sport könnte Arsenal Endrick auf Leihbasis verpflichten.", article)[0]
    assert validate_source_rewrite("Laut BBC Sport könnte Endrick auf Leihbasis zu Arsenal wechseln. Die Leihe ist fest geplant.", article)[0]
    assert validate_source_rewrite("Laut BBC Sport könnte Arsenal Endrick dauerhaft kaufen. Die Leihe ist im Gespräch.", article) == (False, "loan_changed_to_permanent_transfer")
    assert validate_source_rewrite("Laut BBC Sport könnte Endrick zu Arsenal wechseln.", article) == (False, "missing_loan_context")


def test_no_evidence_or_unknown_stage_fails_closed():
    assert validate_source_rewrite("Laut BBC Sport könnte Endrick wechseln.", {**BBC, "source_headline": ""})[1] == "missing_source_evidence"
    assert validate_source_rewrite("Laut BBC Sport könnte Endrick wechseln.", {**BBC, "transfer_status": ""})[1] == "missing_source_stage"


@pytest.mark.parametrize("verb", ["verlängert", "erneuert"])
def test_imminent_renewal_must_not_become_completed_despite_old_rumour_wording(verb):
    article = {**BBC, "source_name": "Mundo Deportivo", "source_headline": "Marc Bernal podría renovar con el Barcelona",
               "source_summary": "", "transfer_type": "extension"}
    rewrite = f"Laut Mundo Deportivo hat Marc Bernal seinen Vertrag {verb}. Zuvor war eine Verlängerung im Gespräch."
    assert validate_source_rewrite(rewrite, article) == (False, "unsupported_completion_claim")
    assert validate_source_rewrite("Laut Mundo Deportivo soll Marc Bernal seinen Vertrag bei Barcelona verlängern.", article)[0]


def test_possible_loan_must_not_become_completed():
    article = {**BBC, "source_headline": "Arsenal interested in Endrick loan", "source_summary": "", "transfer_type": "loan"}
    assert validate_source_rewrite("Laut BBC Sport wurde Endrick ausgeliehen. Zuvor gab es Gerüchte über eine Leihe.", article) == (False, "unsupported_completion_claim")
    assert validate_source_rewrite("Laut BBC Sport könnte Endrick an Arsenal ausgeliehen werden.", article)[0]


def test_live_bernal_confirmation_of_forthcoming_agreement_is_not_completed_renewal():
    article = {**BBC, "source_name": "Mundo Deportivo", "transfer_type": "extension", "evidence_scope": "full",
               "source_headline": "Marc Bernal está cerca de renovar con el FC Barcelona",
               "source_summary": "El propio director deportivo Deco anunció el inmediato acuerdo en la última asamblea."}
    rewrite = ("## Marc Bernal steht vor Vertragsverlängerung beim FC Barcelona\n\n"
               "Laut Mundo Deportivo steht Marc Bernal kurz davor, seinen Vertrag beim FC Barcelona bis 2031 zu verlängern. "
               "Der Mittelfeldspieler wird demnach seine vertragliche Bindung um zwei weitere Jahre ausdehnen. "
               "Der Sportdirektor Deco bestätigte das bevorstehende Einvernehmen während der letzten Versammlung.")
    assert validate_source_rewrite(rewrite, article) == (True, "OK")


@pytest.mark.parametrize("claim", [
    "Der Sportdirektor bestätigte den abgeschlossenen Wechsel.",
    "Der Sportdirektor bestätigte bevorstehenden Wechsel und Endrick hat unterschrieben.",
    "Der Sportdirektor bestätigte den Wechsel während der bevorstehenden Versammlung.",
])
def test_forthcoming_confirmation_exception_does_not_hide_completed_claims(claim):
    rewrite = "Laut BBC Sport könnte Endrick zu Arsenal wechseln. " + claim
    assert validate_source_rewrite(rewrite, BBC) == (False, "unsupported_completion_claim")
