"""Read-only entity names for evidence recognition, without historical club facts."""
import asyncio
import unicodedata

from entity_recognition import PLAYERS_DB, CLUBS_DB


def normalize_alias(value):
    if not isinstance(value, str):
        return ""
    return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()


def _merge_catalogue(static, records):
    # Claim an alias for every named entity before accepting it. A shared surname
    # must never be assigned to the first / most popular database row.
    claims, names = {}, {}

    def claim(alias, name):
        alias, identity = normalize_alias(alias), normalize_alias(name)
        if len(alias) < 2 or not identity or len(alias) > 150:
            return
        names.setdefault(identity, name)
        claims.setdefault(alias, set()).add(identity)

    for alias, item in static.items():
        claim(alias, item["name"])
        claim(item["name"], item["name"])
    static_names = {alias: names[next(iter(owners))] for alias, owners in claims.items() if len(owners) == 1}
    for item in records:
        raw_name = item.get("full_name") or item.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            continue
        raw_name = " ".join(raw_name.split())
        # Only an exact primary name joins a known identity. A shared nickname
        # or surname is not sufficient to merge two different players.
        name = static_names.get(normalize_alias(raw_name), raw_name)
        aliases = item.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        if not isinstance(aliases, (list, tuple)):
            aliases = []
        for alias in [raw_name, item.get("name"), item.get("short_name"), *aliases]:
            claim(alias, name)
    accepted = {alias: {"name": names[next(iter(owners))]}
                for alias, owners in claims.items() if len(owners) == 1}
    ambiguous = sorted(alias for alias, owners in claims.items() if len(owners) > 1)
    return accepted, ambiguous


def build_entity_catalogues(players=(), clubs=()):
    """Pure builder; data fields other than supplied names/aliases are ignored."""
    player_names, player_conflicts = _merge_catalogue(PLAYERS_DB, players)
    club_names, club_conflicts = _merge_catalogue(CLUBS_DB, clubs)
    return {"players": player_names, "clubs": club_names,
            "ambiguous_players": player_conflicts, "ambiguous_clubs": club_conflicts}


async def load_entity_catalogues(db):
    """Load once per processing batch. Read errors propagate for safe retry.

    The projection deliberately excludes current_club, popularity and all other
    metadata: a catalogue resolves a name, never a transfer destination.
    """
    if db is None:
        return build_entity_catalogues()
    projection = {"_id": 0, "name": 1, "full_name": 1, "short_name": 1, "aliases": 1}
    players, clubs = await asyncio.gather(
        db.players.find({}, projection).to_list(length=50000),
        db.clubs.find({}, projection).to_list(length=50000),
    )
    return build_entity_catalogues(players, clubs)
