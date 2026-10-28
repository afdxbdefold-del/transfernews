"""Conservative, offline evidence gate before automatic story/article writes.

Entity popularity and the catalogue's historical club assignments are not evidence.
Unknown or ambiguous reports remain reviewable events rather than invented transfers.
"""
import re

from entity_recognition import PLAYERS_DB, CLUBS_DB
from entity_catalogue import AMBIGUOUS_CLUB_ALIASES, normalize_alias


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
    r"surveille|convoite|veut recruter|intérêt pour|prolongation|renovación|renueva|renovar|renovará|"
    r"neuzugang|unterschreibt|unterzeichnet|piste|rinnovo)\b", re.I)
OFF_TOPIC = re.compile(
    r"\b(?:darts?|golf|tennis|snooker|cricket|handball|charity|benefiz\w*|wohltätig\w*|"
    r"benéfico|beneficenza|caritatif|solidario)\b", re.I)
NON_TRANSFER_HEADLINE = re.compile(
    r"\b(?:injur\w*|verletz\w*|blessure\w*|lesión|lesionado|infortunio|"
    r"match report|spielbericht|spieltag|matchday|scores?|scored|scoring|"
    r"gewinnt|besiegt|sieg|niederlage|defeats?|beats?|medical update|"
    r"geldstrafe\w*|multa\w*|fined|sanction\w*|sanktion\w*|disziplinar\w*|disciplinar\w*)\b", re.I)
NEGATED_MOVE = re.compile(
    r"\b(?:not|never|kein\w*|nicht|no|non|ne|pas|denies|denied|dismissed)\b.{0,35}"
    r"\b(?:join\w*|sign\w*|transfer\w*|wechsel\w*|verpflicht\w*|fich\w*|moves?|"
    r"monitor\w*|eyeing|keen|interest\w*|interesse|interessiert|beobacht\w*|verlänger\w*|"
    r"renew\w*|extend\w*|renov\w*|renuev\w*|ampli\w*|prolong\w*|intéress\w*|surveill\w*|"
    r"agree\w*|deals?|contracts?|boucl\w*|confirm\w*)\b", re.I)
RENEWAL_DENIAL = re.compile(
    r"\b(?:deal|contract|renewal|extension|prolongation|renouvellement)\b[^.!?\n]{0,60}"
    r"\b(?:denied|dismissed|rejected|démenti\w*|dementi\w*|annulé\w*|refusé\w*)\b", re.I)
SOURCE_DENIAL = re.compile(
    r"\b(?:dementiert|dementieren|dementi|denies|denied|refutes?|démenti\w*|dementi\w*|doch\s+nicht)\b", re.I)
CONDITIONAL_MOVE = re.compile(
    r"\b(?:if|unless|wenn|falls|sofern|würde|würden|sollte|sollten|morgen|übermorgen|tomorrow|next week)\b", re.I)

# Complete source-present relations only; a generic 'deal' is not transfer evidence.
# Tokens are produced from resolved names, never from a player's current club.
_RENEWAL_HEADLINE = re.compile(
    r"(?:"
    r"player\s+(?:(?:has|reportedly)\s+){0,2}(?:agrees?|agreed|signs?|signed)\s+(?:a\s+)?new\s+"
    r"(?:(?:one|two|three|four|five|six|seven|eight|nine|ten|\d{1,2})[- ]year\s+)?"
    r"(?:deal|contract)\s+(?:at|with)\s+club"
    r"|player\s+(?:agrees?|agreed|signs?|signed)\s+(?:a\s+)?new\s+club\s+(?:deal|contract)"
    r"|(?:le\s+|l['’])?club\s+(?:(?:a|aurait)\s+)?"
    r"(?:bouclé|officialisé|annoncé|confirmé|acté)\s+(?:la\s+)?"
    r"(?:prolongation|renouvellement)\s+(?:du contrat\s+)?(?:de\s+|d['’])player"
    r"|(?:le\s+|l['’])?club\s+prolonge\s+(?:le contrat de\s+)?player"
    r"|club\s*:\s*player\s+a\s+prolongé"
    r"|player\s+(?:a\s+)?(?:prolonge|prolongé)\s+(?:son contrat\s+)?"
    r"(?:avec|au|à|chez)\s+(?:le\s+)?club"
    r")"
    r"(?:\s*[-–—]\s*(?:(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)['’]s )?gossip)?[.!]?"
)

# A headline-only rewrite has no permission to fill gaps from model knowledge.
# Direct football-position translations share a group. Spanish nationality
# additions require an explicit nationality label: a national-team mention alone
# (e.g. "selección española sub-21") does not establish player nationality.
_FRENCH_MIDFIELD_ROLE = r"milieux?\s+(?:de\s+terrain|offensifs?)"
_FRENCH_FOOTBALL_ROLE = (
    r"(?:" + _FRENCH_MIDFIELD_ROLE +
    r"|joueurs?|footballeurs?|attaquants?|défenseurs?|gardiens?(?:\s+de\s+but)?)"
)
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
    r"türk\w*|turkish|" + _FRENCH_FOOTBALL_ROLE + r"\s+tur(?:c|cs|que|ques)",
    r"japan\w*", r"korea\w*", r"nigerian\w*",
    r"senegales\w*|senegalese", r"marokkan\w*|moroccan\w*", r"uruguay\w*",
    r"kolumbian\w*|colombian\w*", r"ägypt\w*|egyptian\w*",
    r"\d+[- ]?(?:jährig\w*|jahre alt|years?[- ]old)|aged \d+",
    r"jung\w*|young|talent\w*|veteran\w*|routinier\w*",
    r"stürmer\w*|striker\w*|forward\w*|delanter[oa]s?|attaquants?|attaccant[ei]",
    r"mittelfeld\w*|midfielder\w*|centrocampistas?|mediocentros?|mediocampistas?|" + _FRENCH_MIDFIELD_ROLE,
    r"verteidiger\w*|defender\w*|fullback\w*|defensores?|zaguero[as]?|(?:el|un) defensa|défenseurs?|difensor[ei]",
    r"torwart\w*|torhüter\w*|goalkeeper\w*|porter[oa]s?|arquer[oa]s?|gardien de but|portier[ei]",
    r"flügel\w*|winger\w*|extremos?|ailiers?", r"nationalspieler\w*|international player",
    r"geboren|born|aufgewachsen|grew up|karriere\w*|career|jugend\w*|academy|akademie\w*",
    r"tore|goals?|einsätze|appearances|assists?|marktwert|market value",
)


def _journalist_detail(text, match):
    """A reporter's nationality cannot establish the player's nationality."""
    return bool(re.search(r"\b(?:journalist\w*|reporter\w*)\s+$", text[:match.start()], re.I)
                or re.match(r"\s+(?:journalist\w*|reporter\w*)\b", text[match.end():], re.I))


def unsupported_headline_detail(rewrite, evidence, catalogues=None):
    """Reject common biographical additions, including translated football facts."""
    for pattern in HEADLINE_DETAILS:
        expression = r"\b(?:" + pattern + r")\b"
        reported = list(re.finditer(expression, evidence, re.I))
        for detail in re.finditer(expression, rewrite, re.I):
            subject = _journalist_detail(rewrite, detail)
            if not any(_journalist_detail(evidence, item) == subject for item in reported):
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


def _calendar_alias(text, match):
    """Only a dated temporal phrase disambiguates a one-word season surname."""
    return (match[0].casefold() in {"sommer", "winter", "herbst", "frühling", "fruehling"}
            and re.search(r"\b(?:im|zum|vom|(?:seit|ab)(?:[ \t]+dem)?|bis(?:[ \t]+zum)?)[ \t]+$",
                          text[max(0, match.start() - 32):match.start()], re.I)
            and re.match(r"[ \t]+(?:19|20)\d{2}\b", text[match.end():]))


def _mentions(text, catalogue):
    """Longest non-overlapping aliases, with every distinct entity retained."""
    found = []
    for alias, data in catalogue.items():
        for match in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I):
            # The named newspaper is not Athletic Bilbao. Full club names such
            # as Athletic Bilbao remain ordinary longest-match candidates.
            if alias.casefold() == "athletic" and re.search(r"\bthe\s+$", text[:match.start()], re.I):
                continue
            if _calendar_alias(text, match):
                continue
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
        "ambiguous_players": (), "ambiguous_clubs": AMBIGUOUS_CLUB_ALIASES,
    }


# This is deliberately narrower than generic capitalized-word recognition.
# Only complete, source-present names in a football-person relation qualify.
_NAME_WORD = r"[A-ZÀ-ÖØ-Þ][^\W\d_]+(?:[-’'][^\W\d_]+)*"
_FULL_NAME = re.compile(r"(?<!\w)" + _NAME_WORD + r"(?:[ \t]+" + _NAME_WORD + r"){1,3}(?!\w)")
_FULL_CLUB = re.compile(
    r"(?<!\w)(?:(?:FC|FSV|SC|VfB|VfL|TSV|SV|SG|RB|AC|AS|CF|CD|UD|CA)\s+"
    + _NAME_WORD + r"(?:\s+" + _NAME_WORD + r"){0,2}|"
    + _NAME_WORD + r"(?:\s+" + _NAME_WORD + r"){0,2}\s+(?:United|City|Town|Rovers|Wanderers))(?!\w)"
)
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
    r"|\b(?:future of|futuro de|avenir de|piste|new[- ]contract agreement with)\s+)[^.!?;\n]{0,75}$", re.I)
_PERSON_AFTER = re.compile(
    r"^\s+(?:(?:has|will|could|may|is|está|va a|wird|soll|va|ebenfalls|also)\s+){0,3}"
    r"(?:joins?|joined|signs? for|signed for|linked with|linked to|extends?|renews?|"
    r"wechselt|verlängert|unterschreibt|unterzeichnet|verpflichtet|kehrt\s+nach|rejoint|prolonge|renueva|renovará|ampliará)\b", re.I)


def _with_source_clubs(title, summary, catalogues):
    """Preserve complete club names before a short alias can claim their suffix."""
    clubs = dict(catalogues["clubs"])
    conflicts = set(catalogues.get("ambiguous_clubs", ()))
    full_names = []
    for match in _FULL_CLUB.finditer(title + "\n" + summary):
        name = " ".join(match[0].split())
        alias = normalize_alias(name)
        if alias in conflicts:
            continue
        if alias in clubs:
            full_names.append((name, clubs[alias]["name"]))
            continue
        # No merge by surname/suffix: Leeds United is not Manchester United.
        clubs[alias] = {"name": name}
        full_names.append((name, name))
    local_aliases = {}
    for name, identity in full_names:
        short = re.sub(r"^(?:FC|FSV|SC|VfB|VfL|TSV|SV|SG|RB|AC|AS|CF|CD|UD|CA)\s+", "", name)
        if short != name:
            local_aliases.setdefault(normalize_alias(short), set()).add(identity)
    for alias, owners in local_aliases.items():
        if len(owners) == 1 and alias not in clubs and alias not in conflicts:
            clubs[alias] = {"name": next(iter(owners))}
    return {**catalogues, "clubs": clubs}


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
    base = _with_source_clubs(title, summary, _catalogues(catalogues))
    players = dict(base["players"])
    for name in source_player_candidates(title, summary, base):
        alias = normalize_alias(name)
        if alias not in base.get("ambiguous_players", ()):
            players[alias] = {"name": name}
    # A short surname may resolve only to a unique full name actually present
    # in this source; never manufacture a first name from the short form.
    surname_owners = {}
    for item in players.values():
        name = item["name"]
        if " " in name and re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", title + "\n" + summary, re.I):
            surname_owners.setdefault(normalize_alias(name.split()[-1]), set()).add(name)
    for alias, owners in surname_owners.items():
        if len(owners) == 1 and alias not in players and alias not in base.get("ambiguous_players", ()):
            players[alias] = {"name": next(iter(owners))}
    return {**base, "players": players}


def _has_ambiguous_alias(text, aliases, resolved):
    for alias in aliases:
        for match in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I):
            if _calendar_alias(text, match):
                continue
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


def _standalone_renewal(title, catalogues):
    """A whole, unambiguous headline is sufficient evidence for this renewal."""
    if not re.search(r"\b(?:new|prolonge|prolongé|prolongation|renouvellement)\b", title, re.I):
        return None
    players, clubs = _resolved_mentions(title, catalogues)
    if len({item[2] for item in players}) != 1 or len({item[2] for item in clubs}) != 1:
        return None
    if (_has_ambiguous_alias(title, catalogues.get("ambiguous_players", ()), players) or
            _has_ambiguous_alias(title, catalogues.get("ambiguous_clubs", ()), clubs)):
        return None
    player, club = players[0][2], clubs[0][2]
    marked = _mark_mentions(title, players, clubs, {club: "CLUB"}).strip("\"'“”‘’")
    if not _RENEWAL_HEADLINE.fullmatch(marked):
        return None
    return {"player": player, "club": club, "from_club": None,
            "confidence": 1.0, "reason": None, "transfer_type": "extension"}


def _source_units(title, summary):
    """Keep source offsets; no generated paraphrase can become evidence."""
    units = []
    for field, text in (("headline", title), ("summary", summary)):
        matches = [(0, len(text))] if field == "headline" else [
            (m.start(), m.end()) for m in re.finditer(r"[^.!?\n]+(?:[.!?](?=\s|$)|$)", text)]
        for start, end in matches:
            while start < end and text[start].isspace():
                start += 1
            while end > start and text[end - 1].isspace():
                end -= 1
            if start == end or re.match(r"the post\b", text[start:end], re.I):
                continue
            units.append({"field": field, "start": start, "end": end, "text": text[start:end]})
    return units


def _unit_relation(unit, catalogues):
    """Recognize complete relations, never choose an entity by popularity."""
    text = unit["text"]
    if ("?" in text or NEGATED_MOVE.search(text)
            or re.search(r"\b(?:if|unless|wenn|falls|sofern|würde|würden|sollte|sollten|nicht|not|pas|"
                         r"morgen|übermorgen|tomorrow|next week)\b", text, re.I)
            or re.search(r"\b(?:as|als|como)\s+(?:(?:the|new|head|neuer|neuen)\s+){0,2}"
                         r"(?:coach|manager|trainer|entrenador)\b", text, re.I)):
        return None
    players, clubs = _resolved_mentions(text, catalogues)
    if len({p[2] for p in players}) != 1 or not clubs:
        return None
    if (_has_ambiguous_alias(text, catalogues.get("ambiguous_players", ()), players) or
            _has_ambiguous_alias(text, catalogues.get("ambiguous_clubs", ()), clubs)):
        return None
    names = sorted({c[2] for c in clubs})
    tokens = {name: f"CLUB{i}" for i, name in enumerate(names)}
    marked = _mark_mentions(text, players, clubs, tokens).strip('"“”‘’')
    player = players[0][2]
    # A reporter's attribution is removable; it is not a second transfer actor.
    marked = re.sub(r"^(?:according to the athletic|laut [^,]+|selon [^,]+),\s*", "", marked)
    patterns = (
        (r"^player\s+(?:unterschreibt|unterzeichnet)\s+(?:einen vertrag\s+)?(?:bei|beim|für|mit)\s+(?P<club>club\d+)\b",
         "signing", "official"),
        (r"^player\s+hat\s+(?:bei|beim|für)\s+(?P<club>club\d+)\s+(?:einen vertrag\s+)?unterschrieben\b",
         "signing", "official"),
        (r"(?:^|:\s*)(?:[^:]+\s+)?player\s+kehrt\s+(?:nach|zu|zum)\s+(?P<club>club\d+)\s+zurück\b",
         "return", "done"),
        (r"^(?P<club>club\d+)\s*:\s*la piste\s+player\s+(?:est\s+)?relancée\b",
         "interest", "rumor"),
        (r"^(?P<club>club\d+)\s+(?:(?:are|is|reportedly|also|now)\s+){0,3}"
         r"(?:interested in(?: signing)?|monitoring|considering a move for|exploring a move for|keen to sign)\s+"
         r"(?:(?:club\d+)\s+)?(?:(?:attacking |young |promising )?(?:striker|midfielder|defender|goalkeeper|winger|captain)\s+)?player\b",
         "interest", "rumor"),
        (r"^(?P<club>club\d+)\s+(?:(?:are|is|reportedly|confident|they|will|reach|a)\s+){0,9}"
         r"new[- ]contract agreement with\s+player\b", "renewal", "rumor"),
    )
    for pattern, relation, stage in patterns:
        match = re.search(pattern, marked)
        if not match:
            continue
        target = names[int(match["club"][4:])]
        # An explicit origin/role club may remain background in an interest
        # sentence. Other clubs are allowed only when clearly named as opponents.
        for other, token in tokens.items():
            if other == target:
                continue
            token = token.lower()
            role = re.search(rf"\b{token}\s+(?:striker|midfielder|defender|goalkeeper|winger|captain)\s+player\b", marked)
            opponent = re.search(rf"\b(?:gegen|against)\s+{token}\b", marked)
            if not (role or opponent):
                return None
        # A second named person, or an unnamed second signing, is not silently
        # removed by selecting the first complete relation.
        tail = marked[match.end():]
        if re.search(r"\b(?:or|oder|and|und|et|y)\s+(?:player|club\d+|(?:an?\s+)?(?:unnamed|unknown)\s+player)\b", tail):
            return None
        return {"player": player, "club": target, "from_club": None, "confidence": 1.0,
                "reason": None, "relation": relation, "verified_stage": stage,
                **({"transfer_type": "extension"} if relation == "renewal" else {})}
    # Existing verified direction grammars also work at sentence scope. This
    # fallback does not change the established headline-only roundup exception.
    result = _assess_evidence(text, "", catalogues)
    if not result.get("reason"):
        return result
    return None


_CURRENT_RELATION = re.compile(
    r"\b(?:interested|interest in|monitoring|signs?|signed|signing|joins?|unterschreibt|unterzeichnet|wechselt|"
    r"interessiert|umwirbt|surveille|convoite|veut recruter|new[- ]contract|"
    r"competition|race for|battle for|konkurrenz|wettrennen|course pour|concurrence|"
    r"nuevo contrato|contract extension|renews?|extends?|verlängert|vertragsverlängerung|"
    r"prolonge|prolongation|renueva|renovará|ampliará|verpflicht\w*|gibt\b[^.!?]{0,100}\bab)\b", re.I)


def _source_claim_evidence(title, summary, catalogues):
    """Isolate one complete relation; competing current claims stay in review."""
    text = title + "\n" + summary
    if (OFF_TOPIC.search(text) or NON_TRANSFER_HEADLINE.search(title) or NEGATED_MOVE.search(text)
            or SOURCE_DENIAL.search(text)):
        return None
    units = _source_units(title, summary)
    candidates = []
    for unit in units:
        variants = [unit]
        # A trailing squad-building explanation is not the transfer subject.
        # The cut is source-exact and only useful if its prefix independently
        # contains a complete relation.
        aside = re.search(r"\s+as\s+[A-ZÀ-ÖØ-Þ][^.!?]*\blooks?\s+to\s+(?:strengthen|add)\b", unit["text"])
        if aside:
            variants.insert(0, {**unit, "end": unit["start"] + aside.start(), "text": unit["text"][:aside.start()]})
        for variant in variants:
            result = _unit_relation(variant, catalogues)
            if result:
                candidates.append((variant, result))
                break
    if not candidates:
        return None
    identities = {(result["player"], result["club"]) for _, result in candidates}
    if len(identities) != 1:
        return {"reason": "ambiguous_players" if len({x[0] for x in identities}) > 1 else "ambiguous_transfer_direction"}
    chosen, result = candidates[0]
    # Unparsed competing interest/signing clauses cannot be discarded just
    # because another clause matched a familiar grammar.
    for unit in units:
        matched = [item for item, _ in candidates if unit["field"] == item["field"] and unit["start"] == item["start"]]
        remainder = unit["text"]
        if matched:
            # A coach aside may contain another real signing. Check the
            # excluded suffix too instead of exempting the whole sentence.
            remainder = remainder[max(item["end"] for item in matched) - unit["start"]:]
        players, clubs = _resolved_mentions(remainder, catalogues)
        if _CURRENT_RELATION.search(remainder) and (
                {p[2] for p in players} - {result["player"]} or
                {c[2] for c in clubs} - {result["club"]}):
            return {"reason": "ambiguous_players" if {p[2] for p in players} - {result["player"]}
                    else "ambiguous_transfer_direction"}
    spans = [chosen]
    # If the relation uses a short alias, retain the literal full name from this
    # same source as support. This never consults a player's historical club.
    for name in (result["player"], result["club"]):
        if re.search(re.escape(name), chosen["text"], re.I):
            continue
        for field, original in (("headline", title), ("summary", summary)):
            match = re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", original, re.I)
            if match:
                spans.append({"field": field, "start": match.start(), "end": match.end(), "text": match[0]})
                break
    return {**result, "evidence_scope": "claim", "evidence_headline": "\n".join(s["text"] for s in spans),
            "evidence_summary": "", "evidence_spans": spans}


def assess_transfer_evidence(title, summary="", catalogues=None):
    """An explicit standalone headline may be isolated from a mixed roundup.

    This exception uses a complete grammatical claim, not the most popular entity
    or the first sentence of a summary. Its excluded summary is never evidence.
    """
    catalogues = _with_source_players(title, summary, catalogues)
    result = _assess_evidence(title, summary, catalogues)
    # Every output scope must preserve source-level contradiction/conditions.
    # In particular, newly resolved full names must not bypass these safeguards
    # through the earlier successful full/headline path.
    if SOURCE_DENIAL.search(title + "\n" + summary):
        return {"reason": "negated_transfer"}
    if CONDITIONAL_MOVE.search(title + "\n" + summary):
        return {"reason": "ambiguous_transfer_direction"}
    if not result.get("reason"):
        return {**result, "evidence_scope": "full" if summary else "headline"}
    if result["reason"] not in {"ambiguous_players", "ambiguous_clubs", "ambiguous_transfer_direction"}:
        if result["reason"] in {"missing_transfer_context", "unresolved_entities"}:
            return _source_claim_evidence(title, summary, catalogues) or result
        return result  # Topic and negation checks also apply to the excluded summary.
    headline = _assess_evidence(title, "", catalogues)
    if headline.get("reason"):
        return _source_claim_evidence(title, summary, catalogues) or result
    renewal = _standalone_renewal(title, catalogues)
    if renewal:
        # The summary may contain other players or historical clubs. None of it
        # may enter the article once the complete renewal headline is isolated.
        return {**renewal, "evidence_scope": "headline"}
    players, clubs = _resolved_mentions(title, catalogues)
    if len({item[2] for item in clubs}) != 1:
        return _source_claim_evidence(title, summary, catalogues) or result
    marked = _mark_mentions(title, players, clubs, {headline["club"]: "CLUB"})
    standalone = re.fullmatch(
        r"club\s+(?:(?:may|could|might)\s+)?moves? for player"
        r"(?: in (?:january|february|march|april|may|june|july|august|september|october|november|december))?"
        r"(?:\s*[-–—]\s*(?:(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)['’]s )?gossip)?[.!?]?",
        marked,
    )
    return {**headline, "evidence_scope": "headline"} if standalone else (_source_claim_evidence(title, summary, catalogues) or result)


def _assess_evidence(title, summary="", catalogues=None):
    """Return verified names/direction or a stable review reason; never writes."""
    text = f"{title}\n{summary}"
    def reject(reason):
        return {"reason": reason}
    if OFF_TOPIC.search(text) or NON_TRANSFER_HEADLINE.search(title):
        return reject("non_transfer_topic")
    catalogues = _catalogues(catalogues)
    headline_renewal = _standalone_renewal(title, catalogues)
    if not CONTEXT.search(text) and not headline_renewal:
        return reject("missing_transfer_context")
    if NEGATED_MOVE.search(text) or (headline_renewal and RENEWAL_DENIAL.search(text)):
        return reject("negated_transfer")

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
    renewal = len(club_names) == 1 and (headline_renewal or re.search(
        r"\b(?:contract extension|extends? (?:his )?contract|new contract|"
        r"vertragsverlängerung|verlängert.{0,35}vertrag|neuer vertrag|"
        r"prolong(?:e|er|ation).{0,35}contrat|renouvellement|rinnovo|"
        r"(?:renueva|renovará|renovar|ampliar|ampliará|ampliación).{0,40}contrato|"
        r"nuevo contrato|renovación de contrato|(?:renovar|renueva|renovará) a player)\b", marked
    ))
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
