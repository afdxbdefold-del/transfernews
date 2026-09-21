"""Conservative, offline evidence gate before automatic story/article writes.

Entity popularity and the catalogue's historical club assignments are not evidence.
Unknown or ambiguous reports remain reviewable events rather than invented transfers.
"""
import re

from entity_recognition import PLAYERS_DB, CLUBS_DB
from entity_catalogue import normalize_alias


CONTEXT = re.compile(
    r"\b(?:transfers?|transfert|transferts|transferencia|trasferimento|wechsel(?:t|n)?|"
    r"verpflicht(?:et|en|ung)|fichaje|fichar|ficha|recrutement|recruter|"
    r"loan|leihe|leihvertrag|ausleihe|ausgeliehen|prêt|prestito|cesión|cedido|"
    r"vertragsverlängerung|vertragsverlaengerung|vertrag|contract|contrat|contratto|contrato|"
    r"joins?|signs|signed for|signs for|rejoint|firma por|interested in|interest in|"
    r"interesse an|interessiert sich für|interessiert an|interessiert|intéressé par|s'intéresse à|"
    r"interessato a|interesado en|linked (?:with|to)|wants? to sign|moves? for|keen on|"
    r"monitors?|monitoring|eyeing|eyes|keen to sign|beobachtet|umwirbt|wirbt um|im visier|"
    r"bemüht sich um|interés en|interes en|sigue de cerca|quiere fichar|se interesa por|"
    r"surveille|convoite|veut recruter|intérêt pour|prolongation|renovación|renueva|renovar|renovará)\b", re.I)
OFF_TOPIC = re.compile(
    r"\b(?:darts?|golf|tennis|snooker|cricket|charity|benefiz\w*|wohltätig\w*|"
    r"benéfico|beneficenza|caritatif|solidario)\b", re.I)
NON_TRANSFER_HEADLINE = re.compile(
    r"\b(?:injur\w*|verletz\w*|blessure\w*|lesión|lesionado|infortunio|"
    r"match report|spielbericht|spieltag|matchday|scores?|scored|scoring|"
    r"gewinnt|besiegt|sieg|niederlage|defeats?|beats?|medical update)\b", re.I)
NEGATED_MOVE = re.compile(
    r"\b(?:not|never|kein\w*|nicht|no|non|ne|pas|denies|denied|dismissed)\b.{0,35}"
    r"\b(?:join\w*|sign\w*|transfer\w*|wechsel\w*|verpflicht\w*|fich\w*|moves?|"
    r"monitor\w*|eyeing|keen|interest\w*|interesse|interessiert|beobacht\w*|verlänger\w*|"
    r"renew\w*|extend\w*|renov\w*|renuev\w*|ampli\w*|prolong\w*|intéress\w*|surveill\w*)\b", re.I)

# A headline-only rewrite has no permission to fill gaps from model knowledge.
# Direct football-position translations share a group. Spanish nationality
# additions require an explicit nationality label: a national-team mention alone
# (e.g. "selección española sub-21") does not establish player nationality.
HEADLINE_DETAILS = (
    r"brasilian\w*|brazil\w*|nacionalidad\s+brasileña", r"deutsch\w*|german\w*|nacionalidad\s+alemana",
    r"französ\w*|french|nacionalidad\s+francesa",
    r"engländ\w*|englisch\w*|english|nacionalidad\s+inglesa", r"brit\w*|nacionalidad\s+británica",
    r"spani\w*|spanish|nacionalidad\s+española",
    r"portug\w*", r"italien\w*|italian\w*", r"argentini\w*|argentin\w*",
    r"niederländ\w*|holländ\w*|dutch|nacionalidad\s+neerlandesa", r"belg\w*", r"schweiz\w*|swiss|nacionalidad\s+suiza",
    r"österreich\w*|austrian\w*|nacionalidad\s+austríaca", r"dän\w*|danish|nacionalidad\s+danesa",
    r"schwed\w*|swedish|nacionalidad\s+sueca",
    r"norweg\w*|norwegian\w*", r"poln\w*|pole|polish", r"kroat\w*|croatian\w*",
    r"türk\w*|turkish", r"japan\w*", r"korea\w*", r"nigerian\w*",
    r"senegales\w*|senegalese", r"marokkan\w*|moroccan\w*", r"uruguay\w*",
    r"kolumbian\w*|colombian\w*", r"ägypt\w*|egyptian\w*",
    r"\d+[- ]?(?:jährig\w*|jahre alt|years?[- ]old)|aged \d+",
    r"jung\w*|young|talent\w*|veteran\w*|routinier\w*",
    r"stürmer\w*|striker\w*|forward\w*|delanter[oa]s?|attaquants?|attaccant[ei]",
    r"mittelfeld\w*|midfielder\w*|centrocampistas?|mediocentros?|mediocampistas?|milieu de terrain",
    r"verteidiger\w*|defender\w*|fullback\w*|defensores?|zaguero[as]?|(?:el|un) defensa|défenseurs?|difensor[ei]",
    r"torwart\w*|torhüter\w*|goalkeeper\w*|porter[oa]s?|arquer[oa]s?|gardien de but|portier[ei]",
    r"flügel\w*|winger\w*|extremos?|ailiers?", r"nationalspieler\w*|international player",
    r"geboren|born|aufgewachsen|grew up|karriere\w*|career|jugend\w*|academy|akademie\w*",
    r"tore|goals?|einsätze|appearances|assists?|marktwert|market value",
)


def unsupported_headline_detail(rewrite, evidence, catalogues=None):
    """Reject common biographical additions, including translated football facts."""
    for pattern in HEADLINE_DETAILS:
        expression = r"\b(?:" + pattern + r")\b"
        detail = re.search(expression, rewrite, re.I)
        if detail and not re.search(expression, evidence, re.I):
            return f"Unbelegte biografische Angabe in Überschriftenmeldung: {detail[0]}"
    # Do not add a former/current club just because it exists in the name catalogue.
    resolved = _with_source_players(evidence, "", catalogues)
    resolved = _with_source_players(rewrite, "", resolved)
    for reported_mentions, rewritten_mentions in zip(_resolved_mentions(evidence, resolved),
                                                     _resolved_mentions(rewrite, resolved)):
        reported = {item[2] for item in reported_mentions}
        added = {item[2] for item in rewritten_mentions} - reported
        if added:
            return "Unbelegte Person oder Verein in Überschriftenmeldung"
    return None


def _mentions(text, catalogue):
    """Longest non-overlapping aliases, with every distinct entity retained."""
    found = []
    for alias, data in catalogue.items():
        for match in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I):
            # These short surnames are also common grammatical words. Their
            # lowercase forms alone cannot establish a named footballer.
            if alias.casefold() in {"son", "can", "tel"} and match[0].islower():
                continue
            found.append((match.start(), match.end(), data["name"]))
    accepted = []
    for item in sorted(found, key=lambda value: (-(value[1] - value[0]), value[0], value[2])):
        if not any(item[0] >= old[0] and item[1] <= old[1] for old in accepted):
            accepted.append(item)
    return accepted


def _catalogues(catalogues):
    return catalogues if catalogues is not None else {
        "players": PLAYERS_DB, "clubs": CLUBS_DB,
        "ambiguous_players": (), "ambiguous_clubs": (),
    }


# This is deliberately narrower than generic capitalized-word recognition.
# Only complete, source-present names in a football-person relation qualify.
_NAME_WORD = r"[A-ZÀ-ÖØ-Þ][^\W\d_]+(?:[-’'][^\W\d_]+)*"
_FULL_NAME = re.compile(r"(?<!\w)" + _NAME_WORD + r"(?:[ \t]+" + _NAME_WORD + r"){1,3}(?!\w)")
_NAME_STOP = set("the a an el la los las le les der die das ein eine new transfer news "
                 "official deal contract club football sport sunday monday tuesday wednesday "
                 "thursday friday saturday gossip fc cf ac sc real united athletic sporting "
                 "according journalist reporter coach manager trainer entrenador directeur "
                 "director president agent chairman premier league champions liga bundesliga "
                 "unknown unnamed star sensation international former young talent summer winter "
                 "team record breaking release clause academy agency nuevo contrato neuer vertrag "
                 "neues nuevo nueva nouvel nouveau".split())
_PERSON_BEFORE = re.compile(
    r"(?:\b(?:signs?|signed|signing|monitor(?:s|ing)?|eyeing|eyes|interested in|interest in|"
    r"keen to sign|moves? for|beobachtet|umwirbt|verpflichtet|interesse an|interessiert an|"
    r"interessiert sich für|quiere fichar|ficha|interesado en|se interesa por|"
    r"surveille|convoite|recrute|veut recruter|s'intéresse à)\s+(?:a\s+)?"
    r"|\b(?:player|striker|midfielder|defender|goalkeeper|spieler|stürmer|mittelfeldspieler|"
    r"jugador|centrocampista|mediocentro|delantero|futbolista|joueur|attaquant)\s+"
    r"|\b(?:future of|futuro de|avenir de)\s+)[^.!?;\n]{0,75}$", re.I)
_PERSON_AFTER = re.compile(
    r"^\s+(?:(?:has|will|could|may|is|está|va a|wird|soll|va)\s+){0,2}"
    r"(?:joins?|joined|signs? for|signed for|linked with|linked to|extends?|renews?|"
    r"wechselt|verlängert|rejoint|prolonge|renueva|renovará|ampliará)\b", re.I)


def source_player_candidates(title, summary="", catalogues=None):
    """Find transient full player names; no surname guessing or database writes."""
    catalogues = _catalogues(catalogues)
    text = f"{title}\n{summary}"
    if not CONTEXT.search(text):
        return []
    known_players = _mentions(text, catalogues["players"])
    known_clubs = _mentions(text, catalogues["clubs"])
    candidates = []
    for match in _FULL_NAME.finditer(text):
        name = " ".join(match[0].split())
        words = name.split()
        if any(word.casefold() in _NAME_STOP or word.isupper() for word in words):
            continue
        # "Sam Kane" is not Harry Kane just because the surname is known.
        # Only a full recognized span resolves the candidate; an unknown full
        # name wins over a shorter surname when mentions are subsequently marked.
        if any(start <= match.start() and end >= match.end() for start, end, _ in known_players):
            continue
        if any(match.start() < end and match.end() > start for start, end, _ in known_clubs):
            continue
        before = text[max(0, match.start() - 120):match.start()]
        after = text[match.end():match.end() + 120]
        if re.search(r"\b(?:coach|manager|trainer|entrenador|journalist|reporter|director|"
                     r"according to|según|laut|d'après)\s*$", before, re.I):
            continue
        if re.match(r"\s+(?:as|als|como)\s+(?:the |new |head |neuer )?(?:coach|manager|trainer|entrenador)\b", after, re.I):
            continue
        if _PERSON_BEFORE.search(before) or _PERSON_AFTER.search(after):
            if name not in candidates:
                candidates.append(name)
    return candidates


def _with_source_players(title, summary, catalogues):
    base = _catalogues(catalogues)
    players = dict(base["players"])
    for name in source_player_candidates(title, summary, base):
        alias = normalize_alias(name)
        if alias not in base.get("ambiguous_players", ()):
            players[alias] = {"name": name}
    return {**base, "players": players}


def _has_ambiguous_alias(text, aliases, resolved):
    for alias in aliases:
        for match in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I):
            # A complete unambiguous name can disambiguate its shared surname.
            if not any(start <= match.start() and end >= match.end() for start, end, _ in resolved):
                return True
    return False


def _resolved_mentions(text, catalogues):
    players = _mentions(text, catalogues["players"])
    clubs = _mentions(text, catalogues["clubs"])
    # e.g. the club alias "Santos" inside the full player name "André Santos"
    # does not create a second transfer destination (and vice versa).
    players = [item for item in players if not any(
        start <= item[0] and end >= item[1] and end - start > item[1] - item[0]
        for start, end, _ in clubs)]
    clubs = [item for item in clubs if not any(
        start <= item[0] and end >= item[1] and end - start > item[1] - item[0]
        for start, end, _ in players)]
    return players, clubs


def _mark_mentions(text, players, clubs, tokens):
    for start, end, name in sorted(players + clubs, reverse=True):
        text = text[:start] + (tokens[name] if name in tokens else "PLAYER") + text[end:]
    return re.sub(r"\s+", " ", text).lower().strip()


def assess_transfer_evidence(title, summary="", catalogues=None):
    """An explicit standalone headline may be isolated from a mixed roundup.

    This exception uses a complete grammatical claim, not the most popular entity
    or the first sentence of a summary. Its excluded summary is never evidence.
    """
    catalogues = _with_source_players(title, summary, catalogues)
    result = _assess_evidence(title, summary, catalogues)
    if not result.get("reason"):
        return {**result, "evidence_scope": "full" if summary else "headline"}
    if result["reason"] not in {"ambiguous_players", "ambiguous_clubs", "ambiguous_transfer_direction"}:
        return result  # Topic and negation checks also apply to the excluded summary.
    headline = _assess_evidence(title, "", catalogues)
    if headline.get("reason"):
        return result
    players, clubs = _resolved_mentions(title, catalogues)
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


def _assess_evidence(title, summary="", catalogues=None):
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

    catalogues = _catalogues(catalogues)
    players, clubs = _resolved_mentions(text, catalogues)
    if any(player[:2] == club[:2] for player in players for club in clubs):
        return reject("ambiguous_players")
    if _has_ambiguous_alias(text, catalogues.get("ambiguous_players", ()), players):
        return reject("ambiguous_players")
    if _has_ambiguous_alias(text, catalogues.get("ambiguous_clubs", ()), clubs):
        return reject("ambiguous_clubs")
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
            rf"\b{club}\s+(?:(?:is|are|were|reportedly|also|now|closely)\s+){{0,3}}(?:monitors?|monitoring|eyeing|eyes|keen to sign)\s+player\b",
            rf"\b{club}\s+(?:beobachtet|umwirbt|wirbt um|bemüht sich um)\s+player\b",
            rf"\b{club}\s+(?:hat|haben)\s+player\s+im visier\b",
            rf"\b{club}\s+will\s+player\s+verpflichten\b",
            rf"\b{club}\s+(?:ist|zeigt sich)\s+an\s+player\s+interessiert\b",
            rf"\b{club}\s+(?:(?:está|esta|se muestra)\s+)?(?:interesado en|sigue de cerca|quiere fichar a?|se interesa por)\s+player\b",
            rf"\b{club}\s+(?:surveille|convoite|veut recruter|s'intéresse à)\s+player\b",
        ]
        if any(re.search(pattern, marked) for pattern in target_patterns):
            targets.add(name)
        if re.search(rf"\b(?:from|von|vom|aus|de|du|dal|dalla|del|desde)\s+(?:den |dem |le |la |el )?{club}\b", marked):
            origins.add(name)

    # Renewals concern the single explicitly named employer, not a guessed destination.
    renewal = len(club_names) == 1 and re.search(
        r"\b(?:contract extension|extends? (?:his )?contract|new contract|"
        r"vertragsverlängerung|verlängert.{0,35}vertrag|neuer vertrag|"
        r"prolong(?:e|er|ation).{0,35}contrat|renouvellement|rinnovo|"
        r"(?:renueva|renovará|renovar|ampliar|ampliará|ampliación).{0,40}contrato|"
        r"nuevo contrato|renovación de contrato|(?:renovar|renueva|renovará) a player)\b", marked
    )
    if renewal:
        targets.add(club_names[0])
        origins.discard(club_names[0])
    if len(targets) != 1:
        return reject("ambiguous_transfer_direction")
    target = next(iter(targets))
    if target in origins or (len(club_names) == 2 and origins != set(club_names) - {target}):
        return reject("ambiguous_transfer_direction")
    return {"player": next(iter(player_names)), "club": target,
            "from_club": next(iter(origins), None), "confidence": 1.0, "reason": None,
            **({"transfer_type": "extension"} if renewal else {})}
