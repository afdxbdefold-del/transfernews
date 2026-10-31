"""Conservative checks for attributed, source-scoped editorial rewrites.

This is not a general factual-entailment validator. It checks named attribution,
obvious certainty escalation, and renewal/loan transaction drift. Entity, number,
freshness, publisher-host and publication-revision checks remain separate gates.
Only source_headline/source_summary are evidence; prior generated bodies are not.
"""
import re
import unicodedata


def _text(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(char for char in value if not unicodedata.combining(char))


def _words(value):
    return re.sub(r"[^\w]+", " ", _text(value)).strip()


def confirmed_french_renewal(headline, summary, player, club):
    """Require a named renewal and the club's affirmative announcement in the same report."""
    def normalized(value):
        return " ".join(_text(value).replace("’", "'").split())

    person, team = re.escape(normalized(player)), re.escape(normalized(club))
    if not person or not team:
        return False
    named_club = rf"(?:l'|le |la |les )?{team}"
    title = re.fullmatch(rf"{named_club}\s*:\s*{person} prolonge(?: son contrat)? "
                         r"jusqu'en (?P<year>20[0-9]{2})[.!]?", normalized(headline))
    if not title:
        return False
    year = title["year"]
    month = r"(?:janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)"
    until = rf"jusqu'(?:en {year}|au (?:[1-9]|[12][0-9]|3[01]) {month} {year})"
    announced = (r"a (?:annonce|confirme|officialise) "
                 r"(?:(?:ce |le )?(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche) )?"
                 r"la prolongation (?:de |du )?contrat ")
    named_player = rf"(?:de |d'){person}"
    # A reference to "the club" or "the international" needs the preceding
    # official statement identifying both parties. Neither a date nor an
    # isolated "officiel" in an RSS teaser establishes this link.
    identified = (rf"c'est (?:desormais )?officiel\s*:\s*{person} (?:poursuit|continue) "
                  rf"son aventure avec {named_club}\. le club(?: [a-z-]+)? {announced}"
                  rf"(?:{named_player}|du joueur|de l'international(?:e)? [a-z-]+)")
    direct = rf"{named_club} {announced}{named_player}"
    return bool(re.fullmatch(rf"(?:{direct}|{identified}) {until}[.!]?(?:\s*\(\.\.\.\))?",
                             normalized(summary)))


UNCERTAIN = re.compile(
    r"\b(?:konnte\w*|koennte\w*|moglich\w*|moeglich\w*|soll\w*|gerucht\w*|"
    r"geruecht\w*|erwag\w*|erwaeg\w*|interess\w*|rumou?r\w*|may|might|could|"
    r"reportedly|expected|considering|linked|vielleicht|wohl|angeblich|unbestatigt|unbestaetigt)\b|"
    r"\b(?:im gesprach|im gespraech|in verbindung|wird gehandelt|steht aus|noch offen)\b")
IN_PROGRESS = re.compile(
    r"\b(?:verhandel\w*|verhandlung\w*|gesprach\w*|gespraech\w*|bemuh\w*|"
    r"bemueh\w*|talks|negotiations)\b|\b(?:arbeitet an|kurz vor|vor abschluss|"
    r"vor (?:einem |einer |der )?(?:wechsel|unterschrift|(?:vertrags)?verlangerung)|steht bevor)\b")
COMPLETION = re.compile(
    r"\b(?:offiziell\w*|official\w*|bestatigt\w*|bestaetigt\w*|confirmed|"
    r"perfekt|fix|abgeschlossen|completed|unterschrieben|unterzeichnet|"
    r"verpflichtet|gewechselt|wechselt|wechselte|unterschreibt|joins|signed|announced|announces|"
    r"verlangert|verlaengert|erneuert|ausgeliehen|verliehen|loaned|renewed|extends|extended|renueva|renovo|renovado|rinnova)\b|"
    r"\bsichert\s+sich\b|\bunter\s+vertrag\s+genommen\b|"
    r"\bnimmt\b[^.!?;\n]{0,50}\bunter\s+vertrag\b|"
    r"\b(?:kein|nicht mehr)\s+(?:gerucht|geruecht|rumou?r)\b")
RENEWAL = re.compile(
    r"\b(?:(?:vertrags)?verlanger\w*|(?:vertrags)?verlaenger\w*|"
    r"erneuer\w*|renew\w*|extend\w*|extension|renov\w*|renueva\w*|rinnovo\w*|prolong\w*)\b")
LOAN = re.compile(r"\b(?:leih\w*|leihe|ausgelieh\w*|verlieh\w*|loan\w*|prestito|cesion|pret)\b")
MOVE = re.compile(
    r"\b(?:wechselt|wechselte|wechseln|gewechselt|joins?|joining|moves?|moving|"
    r"verpflichtet|holt|ablose|abloese)\b|\b(?:transfer|wechsel)\s+(?:von|zu|zum|nach)\b")
PERMANENT = re.compile(
    r"\b(?:dauerhaft\w*|permanent\w*|endgultig\w*|endgueltig\w*|gekauft|"
    r"kauft|kaufen|kauf)\b|\bfest(?:e[nrms]?)?\s+(?:verpflicht\w*|wechsel|transfer)\b")

# Agreement/renewal is not evidence of a signature, even when the generated
# signature claim is qualified with "soll" or "könnte".
SIGNATURE = re.compile(
    r"\b(?:unterschr(?:ieben|ieb\w*|eibt|eiben)|unterzeichn\w*|signiert\w*|"
    r"sign|signed|signs|signing|signe|signee|signes|signees|signato|signata|firmado|firmada|firmo)\b")
DETAILS = r"\b(?:details|informationen|infos|einzelheiten|angaben|information|informacion|detalles)\b"
HEADLINE_FILLER = (
    (re.compile(DETAILS + r"[^.!?;\n]{0,90}\b(?:unklar\w*|unbekannt\w*|offen|unclear|unknown)\b"),
     re.compile(DETAILS + r"[^.!?;\n]{0,90}\b(?:unklar\w*|unbekannt\w*|offen|unclear|unknown|desconocid\w*)\b")),
    (re.compile(DETAILS + r"[^.!?;\n]{0,90}\b(?:unbestatigt\w*|unbestaetigt\w*|nicht\s+bestatigt|unconfirmed)\b"),
     re.compile(DETAILS + r"[^.!?;\n]{0,90}\b(?:unbestatigt\w*|unbestaetigt\w*|nicht\s+bestatigt|unconfirmed|not\s+confirmed|sin\s+confirmar)\b")),
    (re.compile(DETAILS + r"[^.!?;\n]{0,90}\b(?:aussteh\w*|stehen\s+(?:noch\s+)?aus|fehlen\w*|"
                r"nicht\s+(?:bekannt|veroffentlicht|bekanntgegeben|genannt)|liegen\s+(?:noch\s+)?nicht\s+vor)\b"),
     re.compile(DETAILS + r"[^.!?;\n]{0,90}\b(?:aussteh\w*|stehen\s+(?:noch\s+)?aus|fehlen\w*|"
                r"nicht\s+(?:bekannt|veroffentlicht|bekanntgegeben|genannt)|liegen\s+(?:noch\s+)?nicht\s+vor|"
                r"not\s+(?:yet\s+)?(?:available|disclosed|released|announced)|remain\s+undisclosed|pending)\b")),
)


def _clause_context(text, match):
    # A modal in an earlier sentence/contrasting clause does not qualify a claim.
    before = re.split(r"[.!?;\n,]|\b(?:aber|jedoch|doch|und)\b", text[:match.start()])[-1][-100:]
    after = re.split(r"[.!?;\n,]|\b(?:aber|jedoch|doch|und)\b", text[match.end():])[0][:60]
    return before, after


def _negated(text, match):
    before, after = _clause_context(text, match)
    # Negation must attach to the claim, not to an unrelated manner phrase such
    # as "ohne Zögern unterschrieben" or "ohne Zweifel bestätigt".
    return bool(re.search(
        r"\b(?:nicht|not|kein\w*|weder|never|no)\s+"
        r"(?:(?:bereits|schon|offiziell|officially|yet|a|any|the|der|dem|eine?[nrms]?|den|nun)\s+){0,3}$", before)
        or re.search(r"\b(?:ohne|without)\s+(?:(?:eine?[nrms]?|den|dem|the|a|any)\s+)?$", before)
        or re.search(r"\bweder\b.{0,60}\bnoch\s*$", before)
        or re.search(r"\bkein\w*\s+(?:wechsel|transfer|vertrag|unterschrift)\s+(?:ist|wurde|sei|wird)\s*$", before)
        or re.match(r"\s+(?:(?:ist|sei|wurde|wird|sind|bleibt)\s+)?(?:noch\s+)?(?:nicht|kein\w*)\b", after))


def _asserted_completions(text):
    for match in COMPLETION.finditer(text):
        before, after = _clause_context(text, match)
        # Confirming talks or a directly named forthcoming agreement does not
        # confirm completion. Other completion verbs in the clause still apply.
        if re.fullmatch(r"(?:bestatigt\w*|bestaetigt\w*|confirmed)", match.group()):
            if re.match(r"\s+(?:(?:das|sein|ihr|the)\s+)?(?:interesse|interest|gesprache|talks|verhandlungen)\b", after):
                continue
            if re.match(
                    r"\s+(?:(?:das|den|die|ein|eine|einen)\s+)?bevorstehende[nrms]?\s+"
                    r"(?:einvernehmen|einigung|vertrags(?:verlangerung|verlaengerung|abschluss|unterzeichnung)|"
                    r"unterschrift|wechsel|transfer|bekanntgabe|ankundigung|ankuendigung)\b", after):
                continue
        post_modal = re.match(
            r"^\s*(?:\w+\s+){0,4}(?:moglicherweise|moeglicherweise|vielleicht|wohl|angeblich|reportedly)\b", after)
        if (not _negated(text, match) and not UNCERTAIN.search(before)
                and not IN_PROGRESS.search(before) and not UNCERTAIN.match(after.lstrip()) and not post_modal):
            yield match


def _positive_signature(text, match):
    before, after = _clause_context(text, match)
    return not (_negated(text, match)
                or re.search(r"\b(?:pas|jamais|non|sin|sans|denies|denied|denying|refused)\s+(?:having\s+)?$", before)
                or re.match(r"\s+(?:has\s+been\s+|was\s+|is\s+)?(?:denied|dementi\w*)\b", after))


def _attributed(text, publisher):
    name = _words(publisher)
    if not name:
        return False
    words = _words(text)
    escaped = re.escape(name)
    # Punctuation/diacritics/Markdown may differ; the publisher name must not.
    return bool(re.search(
        r"\b(?:laut|nach (?:angaben|informationen|berichten)(?: von)?|bericht(?: von)?|quelle)\s+(?:(?:der|dem|von)\s+)?" + escaped + r"\b", words)
        or re.search(r"\b" + escaped + r"\s+(?:berichtet|meldet|schreibt|zufolge|reports|says)\b", words)
        or re.search(r"\bwie\s+" + escaped + r"\b.{0,50}\b(?:berichtet|meldet|schreibt)\b", words))


def validate_source_rewrite(rewrite, article):
    """Return (accepted, reason) without network, database, or model calls."""
    headline = article.get("source_headline") or ""
    summary = "" if article.get("evidence_scope") in {"headline", "claim"} else article.get("source_summary") or ""
    evidence = _text(headline + "\n" + summary)
    if not evidence.strip():
        return False, "missing_source_evidence"
    publisher = article.get("source_name") or article.get("primary_source") or ""
    if not _attributed(rewrite, publisher):
        return False, "missing_named_source_attribution"
    text = _text(rewrite)
    stage = _text(article.get("transfer_status") or article.get("current_stage"))
    if stage == "rumour":
        stage = "rumor"
    if stage not in {"rumor", "advanced", "near_done", "done", "official"}:
        return False, "missing_source_stage"
    claims = list(_asserted_completions(text))
    if stage in {"rumor", "advanced", "near_done"}:
        if claims:
            return False, "unsupported_completion_claim"
        if not UNCERTAIN.search(text) and not IN_PROGRESS.search(text):
            return False, "missing_transfer_uncertainty"
    elif claims and not (list(_asserted_completions(evidence)) or
                         (stage == "official" and article.get("transfer_type") == "extension"
                          and confirmed_french_renewal(headline, summary, article.get("player_name"),
                                                       article.get("club_name")))):
        # A stage label alone is not a source for completion wording.
        return False, "unsupported_completion_claim"

    if (any(_positive_signature(text, match) for match in SIGNATURE.finditer(text))
            and not any(_positive_signature(evidence, match) for match in SIGNATURE.finditer(evidence))):
        return False, "unsupported_signature_claim"
    if article.get("evidence_scope") in {"headline", "claim"}:
        for output_pattern, source_pattern in HEADLINE_FILLER:
            if output_pattern.search(text) and not source_pattern.search(evidence):
                return False, "unsupported_headline_filler"

    kind = _text(article.get("transfer_type"))
    renewal = kind in {"extension", "renewal"} or bool(RENEWAL.search(evidence))
    loan = kind == "loan" or (not renewal and bool(LOAN.search(evidence)))
    if renewal:
        if any(not _negated(text, match) for match in MOVE.finditer(text)):
            return False, "renewal_changed_to_transfer"
        if not RENEWAL.search(text):
            return False, "missing_renewal_context"
    if loan:
        if any(not _negated(text, match) for match in PERMANENT.finditer(text)):
            return False, "loan_changed_to_permanent_transfer"
        if not LOAN.search(text):
            return False, "missing_loan_context"
    return True, "OK"
