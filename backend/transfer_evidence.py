"""Conservative, offline evidence gate before automatic story/article writes.

Entity popularity and the catalogue's historical club assignments are not evidence.
Unknown or ambiguous reports remain reviewable events rather than invented transfers.
"""
import re

from entity_recognition import PLAYERS_DB, CLUBS_DB


CONTEXT = re.compile(
    r"\b(?:transfers?|transfert|transferts|transferencia|trasferimento|wechsel(?:t|n)?|"
    r"verpflicht(?:et|en|ung)|fichaje|fichar|ficha|recrutement|recruter|"
    r"loan|leihe|leihvertrag|ausleihe|ausgeliehen|prêt|prestito|cesión|cedido|"
    r"vertragsverlängerung|vertragsverlaengerung|vertrag|contract|contrat|contratto|contrato|"
    r"joins?|signed for|signs for|rejoint|firma por|interested in|interest in|"
    r"interesse an|interessiert sich für|interessiert an|intéressé par|s'intéresse à|"
    r"interessato a|interesado en|linked (?:with|to)|wants? to sign|moves? for|keen on)\b", re.I)
OFF_TOPIC = re.compile(
    r"\b(?:darts?|golf|tennis|snooker|cricket|charity|benefiz\w*|wohltätig\w*|"
    r"benéfico|beneficenza|caritatif|solidario)\b", re.I)
NON_TRANSFER_HEADLINE = re.compile(
    r"\b(?:injur\w*|verletz\w*|blessure\w*|lesión|lesionado|infortunio|"
    r"match report|spielbericht|spieltag|matchday|scores?|scored|scoring|"
    r"gewinnt|besiegt|sieg|niederlage|defeats?|beats?|medical update)\b", re.I)
NEGATED_MOVE = re.compile(
    r"\b(?:not|never|kein\w*|nicht|no|non|pas|denies|denied|dismissed)\b.{0,35}"
    r"\b(?:join\w*|sign\w*|transfer\w*|wechsel\w*|verpflicht\w*|fich\w*|moves?)\b", re.I)


def _mentions(text, catalogue):
    """Longest non-overlapping aliases, with every distinct entity retained."""
    found = []
    for alias, data in catalogue.items():
        for match in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I):
            found.append((match.start(), match.end(), data["name"]))
    accepted = []
    for item in sorted(found, key=lambda value: (-(value[1] - value[0]), value[0], value[2])):
        if not any(item[0] >= old[0] and item[1] <= old[1] for old in accepted):
            accepted.append(item)
    return accepted


def _mark_mentions(text, players, clubs, tokens):
    for start, end, name in sorted(players + clubs, reverse=True):
        text = text[:start] + (tokens[name] if name in tokens else "PLAYER") + text[end:]
    return re.sub(r"\s+", " ", text).lower().strip()


def assess_transfer_evidence(title, summary=""):
    """An explicit standalone headline may be isolated from a mixed roundup.

    This exception uses a complete grammatical claim, not the most popular entity
    or the first sentence of a summary. Its excluded summary is never evidence.
    """
    result = _assess_evidence(title, summary)
    if not result.get("reason"):
        return {**result, "evidence_scope": "full" if summary else "headline"}
    if result["reason"] not in {"ambiguous_players", "ambiguous_clubs", "ambiguous_transfer_direction"}:
        return result  # Topic and negation checks also apply to the excluded summary.
    headline = _assess_evidence(title, "")
    if headline.get("reason"):
        return result
    players, clubs = _mentions(title, PLAYERS_DB), _mentions(title, CLUBS_DB)
    if len({item[2] for item in clubs}) != 1:
        return result
    marked = _mark_mentions(title, players, clubs, {headline["club"]: "CLUB"})
    standalone = re.fullmatch(
        r"club\s+(?:(?:may|could|might)\s+)?moves? for player"
        r"(?: in (?:january|february|march|april|may|june|july|august|september|october|november|december))?"
        r"(?:\s*[-–—]\s*(?:(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)['’]s )?gossip)?[.!?]?",
        marked,
    )
    return {**headline, "evidence_scope": "headline"} if standalone else result


def _assess_evidence(title, summary=""):
    """Return verified names/direction or a stable review reason; never writes."""
    text = f"{title}\n{summary}"
    def reject(reason):
        return {"reason": reason}
    if OFF_TOPIC.search(text) or NON_TRANSFER_HEADLINE.search(title):
        return reject("non_transfer_topic")
    if not CONTEXT.search(text):
        return reject("missing_transfer_context")
    if NEGATED_MOVE.search(text):
        return reject("negated_transfer")

    players = _mentions(text, PLAYERS_DB)
    clubs = _mentions(text, CLUBS_DB)
    player_names = {item[2] for item in players}
    club_names = sorted({item[2] for item in clubs})
    if not player_names or not club_names:
        return reject("unresolved_entities")
    if len(player_names) != 1:
        return reject("ambiguous_players")
    if len(club_names) > 2:
        return reject("ambiguous_clubs")

    # Replace actual mentions so all aliases have identical direction semantics.
    tokens = {name: f"CLUB{i}" for i, name in enumerate(club_names)}
    marked = _mark_mentions(text, players, clubs, tokens)
    targets, origins = set(), set()
    for name, token in tokens.items():
        club = token.lower()
        # Direction prepositions are considered only in explicit transfer context.
        target_patterns = [
            rf"\b(?:to|zu|zum|zur|nach|vers|chez|à|a|al|alla|hacia)\s+(?:den |dem |le |la |el )?{club}\b",
            rf"\b(?:joins?|joined|rejoint|signed for|signs for|firma por|ficha por|linked with|linked to|loan at|leihe bei)\s+{club}\b",
            rf"\b{club}\b[^.!?;]{{0,65}}\b(?:interested in|interest in|keen on|wants? to sign|interesse an|interessiert sich für|interessiert an|intéressé par|s'intéresse à|interessato a|interesado en)\s+(?:signing )?player\b",
            rf"\b{club}\s+(?:(?:has|have|hat|haben|officially|offiziell)\s+){{0,2}}(?:signs?|signed|verpflichtet|leiht|recrute|recruté|ficha)\s+player\b",
            rf"\b{club}\s+(?:(?:may|could|might)\s+)?moves? for player\b",
        ]
        if any(re.search(pattern, marked) for pattern in target_patterns):
            targets.add(name)
        if re.search(rf"\b(?:from|von|vom|aus|de|du|dal|dalla|del|desde)\s+(?:den |dem |le |la |el )?{club}\b", marked):
            origins.add(name)

    # Renewals concern the single explicitly named employer, not a guessed destination.
    if len(club_names) == 1 and re.search(
        r"\b(?:contract extension|extends? (?:his )?contract|new contract|"
        r"vertragsverlängerung|verlängert.{0,35}vertrag|neuer vertrag|"
        r"prolonge.{0,35}contrat|renouvellement|rinnovo|renueva.{0,35}contrato)\b", marked
    ):
        targets.add(club_names[0])
        origins.discard(club_names[0])
    if len(targets) != 1:
        return reject("ambiguous_transfer_direction")
    target = next(iter(targets))
    if target in origins or (len(club_names) == 2 and origins != set(club_names) - {target}):
        return reject("ambiguous_transfer_direction")
    return {"player": next(iter(player_names)), "club": target,
            "from_club": next(iter(origins), None), "confidence": 1.0, "reason": None}
