"""One-time reversible takeover repair; default is a read-only plan.

Run with application writers stopped and a separately verified restore backup.
Every changed/deleted source record is archived before mutation.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
from pymongo import MongoClient, ASCENDING

MIGRATION = "20260920_takeover_v1"
WIRTZ_KEEP = "1e66c615-6d89-4ce6-91de-9b70e8051361"
WIRTZ_DUPLICATE = "50c7ef6a-4c52-46cd-a280-306514d07177"
WIRTZ_CLUB = "13b9e096-ec72-4150-8c2b-ea5fa8da8312"
INDEXES = [
    ("articles", [("slug", 1)], {"unique": True, "name": "article_slug_unique"}),
    ("articles", [("status", 1), ("published_at", -1)], {"name": "published_articles"}),
    ("articles", [("needs_gpt_rewrite", 1), ("rewrite_next_attempt_at", 1)], {"name": "rewrite_queue"}),
    ("events", [("status", 1), ("next_attempt_at", 1), ("created_at", 1)], {"name": "event_queue"}),
    ("events", [("source_url", 1)], {"name": "event_source_url"}),
    ("transfer_stories", [("story_key", 1)], {"unique": True, "partialFilterExpression": {"story_key": {"$type": "string"}}, "name": "story_identity_unique"}),
]


def utc(value):
    if isinstance(value, str):
        try: value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError: return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return None


def fingerprint(rows):
    content = json.dumps(sorted(rows, key=lambda r: str(r["_id"])), default=str, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content.encode()).hexdigest()


def unique_identity(base, identity, reserved, separator="-", max_length=None):
    digest = hashlib.sha256(str(identity).encode()).hexdigest()
    for length in range(12, 65, 4):
        prefix = base[:max_length-length-len(separator)] if max_length else base
        candidate = prefix + separator + digest[:length]
        if candidate not in reserved:
            reserved.add(candidate)
            return candidate
    counter = 1
    while True:
        suffix = digest + separator + str(counter)
        prefix = base[:max_length-len(suffix)-len(separator)] if max_length else base
        candidate = prefix + separator + suffix
        if candidate not in reserved:
            reserved.add(candidate)
            return candidate
        counter += 1


def completed(db):
    return bool(db.repair_runs.find_one({"_id": MIGRATION, "completed_at": {"$exists": True}}))


def remap_player_references(value):
    """Only remap schema-defined IDs; unknown occurrences stop this targeted merge."""
    if isinstance(value, list):
        return [remap_player_references(item) for item in value]
    if not isinstance(value, dict):
        if value == WIRTZ_DUPLICATE:
            raise RuntimeError("Unknown retired player ID reference requires manual review; no data was changed")
        return value
    result = {}
    for field, item in value.items():
        if field == "player_id" or (field == "entity_id" and value.get("entity_type") == "player"):
            result[field] = WIRTZ_KEEP if item == WIRTZ_DUPLICATE else item
        elif field in {"linked_player_ids", "player_ids"} and isinstance(item, list):
            result[field] = list(dict.fromkeys(WIRTZ_KEEP if identity == WIRTZ_DUPLICATE else identity for identity in item))
        else:
            result[field] = remap_player_references(item)
    return result


def plan_player_merge(db, result, now):
    """Merge only the two independently verified inherited Wirtz records."""
    players = list(db.players.find({"id": {"$in": [WIRTZ_KEEP, WIRTZ_DUPLICATE]}}))
    keeper = next((row for row in players if row.get("id") == WIRTZ_KEEP), None)
    retired = next((row for row in players if row.get("id") == WIRTZ_DUPLICATE), None)
    if retired is None:
        return
    if len(players) != 2 or keeper is None:
        raise RuntimeError("Targeted player merge needs exactly one source and one canonical player")
    if (keeper.get("slug") != "wirtz" or retired.get("slug") != "florian-wirtz"
            or any(row.get("name") != "Florian Wirtz" or row.get("position") != "Midfielder" for row in players)
            or keeper.get("current_club_id") != WIRTZ_CLUB
            or retired.get("current_club_id") not in (None, "", WIRTZ_CLUB)):
        raise RuntimeError("Targeted player identity differs from the verified records; no data was changed")
    for field in ("birthdate", "birth_date", "nationality", "country"):
        if retired.get(field) and retired.get(field) != keeper.get(field):
            raise RuntimeError("Targeted player merge has conflicting biographical data; manual review required")
    if db.players.count_documents({"slug": {"$in": ["wirtz", "florian-wirtz"]}}) != 2:
        raise RuntimeError("Targeted player slugs are ambiguous; manual review required")
    aliases = list(db.aliases.find({"entity_type": "player", "normalized_alias": "florian-wirtz"}))
    if len(aliases) > 1 or any(row.get("entity_id") not in {WIRTZ_KEEP, WIRTZ_DUPLICATE} for row in aliases):
        raise RuntimeError("Retired player alias is already assigned ambiguously; manual review required")
    # Inspect all application collections, including legacy schemas. Unknown ID fields abort
    # rather than silently dropping a reference or replacing prose/content strings.
    names = sorted({"players", "aliases", *(name for name in db.list_collection_names() if not name.startswith(("repair_", "system.")))})
    for name in names:
        rows = list(db[name].find({}))
        result["snapshot"][name] = fingerprint(rows)
        for row in rows:
            if name == "players" and row.get("id") == WIRTZ_DUPLICATE:
                continue
            remapped = remap_player_references(row)
            fields = {field: value for field, value in remapped.items() if row.get(field) != value}
            if fields:
                result["entity_updates"].setdefault(name, {})[row["_id"]] = fields
    retained_aliases = list(dict.fromkeys([*(keeper.get("aliases") or []), *(retired.get("aliases") or []), "florian-wirtz"]))
    result["entity_updates"].setdefault("players", {}).setdefault(keeper["_id"], {})["aliases"] = retained_aliases
    result["retired_player"] = retired["_id"]
    fields = {"entity_type": "player", "entity_id": WIRTZ_KEEP, "alias": "florian-wirtz", "normalized_alias": "florian-wirtz"}
    if aliases:
        result["entity_updates"].setdefault("aliases", {}).setdefault(aliases[0]["_id"], {}).update(fields)
    else:
        identity = MIGRATION + ":player-alias:florian-wirtz"
        if db.aliases.find_one({"_id": identity}) or db.aliases.find_one({"id": identity}):
            raise RuntimeError("Generated player alias ID already exists; manual review required")
        result["new_player_alias"] = {"_id": identity, "id": identity, **fields, "created_at": now, "repair_migration": MIGRATION}


def plan(db, now):
    result = {"articles": {}, "stories": {}, "old_events": [], "entity_updates": {}, "retired_player": None, "new_player_alias": None,
              "duplicates": 0, "cutoff": now-timedelta(hours=48), "already_completed": completed(db)}
    if result["already_completed"]:
        return result
    documents = {name: list(db[name].find({})) for name in ("articles", "transfer_stories", "events", "authors")}
    result["snapshot"] = {name: fingerprint(rows) for name, rows in documents.items()}
    articles = documents["articles"]
    authors = documents["authors"]
    author_ids = {a.get("id") for a in authors if a.get("id")}
    author_slugs = {a.get("slug") for a in authors if a.get("slug")}
    author_names = {a.get("name") for a in authors if a.get("name")}
    editorial = next((a for a in authors if a.get("slug") == "redaktion"), {})
    groups = defaultdict(list)
    changes = result["articles"]
    reserved_slugs = {a["slug"] for a in articles if isinstance(a.get("slug"), str) and a["slug"]}
    for article in articles:
        slug = article.get("slug") if isinstance(article.get("slug"), str) else ""
        groups[slug or ""].append(article)
        values = {}
        publication_time = utc(article.get("published_at")) or utc(article.get("created_at"))
        if publication_time and publication_time < result["cutoff"]:
            values.update(needs_gpt_rewrite=False, rewrite_status="review", rewrite_review_reason="historical_content")
        known_author = (article.get("author_id") in author_ids or article.get("author_slug") in author_slugs or article.get("author_name") in author_names)
        if not known_author:
            values.update(author_name="Redaktion", author_slug="redaktion", author_id=editorial.get("id", "redaktion"), author_role="Redaktion", author_image=None)
        unknown = str(article.get("player_name", "")).strip().lower() in {"unbekannt", "unbekannter spieler", "unknown", "unknown player"}
        unknown = unknown or "unbekannter spieler" in str(article.get("title", "")).lower()
        if unknown:
            values.update(status="draft", review_reason="unresolved_player_in_inherited_article", needs_gpt_rewrite=False)
        if values: changes[article["_id"]] = values
    canonical_ids = {}
    for slug in sorted(groups):
        docs = groups[slug]
        docs.sort(key=lambda d: (d.get("status") != "published", utc(d.get("published_at")) or utc(d.get("created_at")) or now, str(d["_id"])))
        keep = docs[0]
        for index, doc in enumerate(docs):
            values = changes.setdefault(doc["_id"], {})
            new_slug = slug
            if not slug or index:
                new_slug = unique_identity(slug or "artikel", doc["_id"], reserved_slugs, max_length=240)
                values.update(slug=new_slug, original_slug=slug)
                if index:
                    result["duplicates"] += 1
                    values.update(status="draft", duplicate_of=keep.get("id"), review_reason="duplicate_in_inherited_data", needs_gpt_rewrite=False)
                    if doc.get("id") and keep.get("id"): canonical_ids[doc["id"]] = keep["id"]
            canonical = "https://transfernews.de/news/" + new_slug
            if doc.get("canonical_url") != canonical: values["canonical_url"] = canonical
    for article in articles:
        if article.get("id") and article.get("duplicate_of"):
            canonical_ids.setdefault(article["id"], article["duplicate_of"])
    def canonical_article(identity):
        seen = set()
        while identity in canonical_ids and identity not in seen:
            seen.add(identity); identity = canonical_ids[identity]
        return identity
    pending = {"pending", "retry", "review", "error", "processing"}
    for event in documents["events"]:
        source_time = utc(event.get("source_published_at")) or utc(event.get("published_at")) or utc(event.get("created_at"))
        if event.get("status") in pending and source_time and source_time < result["cutoff"]:
            result["old_events"].append(event["_id"])
    stories = defaultdict(list)
    all_stories = documents["transfer_stories"]
    reserved_keys = {s["story_key"] for s in all_stories if isinstance(s.get("story_key"), str)}
    story_changes = result["stories"]
    article_map = {a["id"]: a for a in articles if a.get("id")}
    for story in all_stories:
        key = story.get("story_key")
        if not isinstance(key, str) or not key.strip():
            story_changes[story["_id"]] = {"repair_archived": True, "repair_original_story_key": key,
                "story_key": unique_identity("legacy:missing:archived", story["_id"], reserved_keys, separator=":")}
            continue
        stories[key].append(story)
        mapped = canonical_article(story.get("article_id"))
        if mapped != story.get("article_id") and mapped in article_map:
            story_changes.setdefault(story["_id"], {})["article_id"] = mapped
    for key in sorted(stories):
        docs = stories[key]
        def rank(story):
            article = article_map.get(canonical_article(story.get("article_id")), {})
            merged = {**article, **changes.get(article.get("_id"), {})}
            return (bool(story.get("repair_archived")), merged.get("status") != "published", utc(story.get("created_at")) or now, str(story["_id"]))
        docs.sort(key=rank)
        for doc in docs[1:]:
            story_changes.setdefault(doc["_id"], {}).update(repair_archived=True, repair_original_story_key=key,
                story_key=unique_identity(key + ":archived", doc["_id"], reserved_keys, separator=":"))
    originals = {a["_id"]: a for a in articles}
    result["articles"] = {key: {f: v for f,v in values.items() if originals[key].get(f) != v} for key,values in changes.items()}
    result["articles"] = {key: values for key,values in result["articles"].items() if values}
    plan_player_merge(db, result, now)
    preflight(db, result)
    return result


def preflight(db, operations):
    """Validate all final identities and source snapshots before any write."""
    for name, digest in operations.get("snapshot", {}).items():
        if fingerprint(list(db[name].find({}))) != digest:
            raise RuntimeError("Migration source changed after planning; stop writers and re-plan")
    for collection, field, key in (("articles", "slug", "articles"), ("transfer_stories", "story_key", "stories")):
        seen = set()
        for row in db[collection].find({}):
            value = operations.get(key, {}).get(row["_id"], {}).get(field, row.get(field))
            if collection == "articles" and (not isinstance(value, str) or not value):
                raise RuntimeError("Final article slugs must be nonempty strings")
            if collection == "transfer_stories" and not isinstance(value, str): continue
            if value in seen: raise RuntimeError("Migration would leave duplicate identities; no data was changed")
            seen.add(value)
    for collection, keys, options in INDEXES:
        existing = db[collection].index_information().get(options["name"])
        if existing and (list(existing["key"]) != keys or bool(existing.get("unique")) != bool(options.get("unique"))
                         or existing.get("partialFilterExpression") != options.get("partialFilterExpression")):
            raise RuntimeError("Conflicting named index requires manual review before migration")


def ensure_indexes(db):
    for collection, keys, options in INDEXES:
        equivalent = any(list(info["key"]) == keys and bool(info.get("unique")) == bool(options.get("unique"))
            and info.get("partialFilterExpression") == options.get("partialFilterExpression") for info in db[collection].index_information().values())
        if not equivalent: db[collection].create_index(keys, **options)


def apply(db, operations):
    if completed(db):
        preflight(db, {})
        ensure_indexes(db)
        return 0
    preflight(db, operations)
    archive = db.repair_archive
    def preserve(collection, identity):
        document = db[collection].find_one({"_id": identity})
        if document is None: raise RuntimeError("Source record disappeared before mutation")
        key = MIGRATION + ":" + collection + ":" + str(identity)
        archive.update_one({"_id": key}, {"$setOnInsert": {"migration": MIGRATION, "collection": collection, "document": document}}, upsert=True)
    for collection, key in (("articles", "articles"), ("transfer_stories", "stories")):
        for identity, values in operations[key].items():
            preserve(collection, identity)
            db[collection].update_one({"_id": identity}, {"$set": {**values, "repair_migration": MIGRATION}})
    for collection, updates in operations.get("entity_updates", {}).items():
        for identity, values in updates.items():
            preserve(collection, identity)
            db[collection].update_one({"_id": identity}, {"$set": {**values, "repair_migration": MIGRATION}})
    new_alias = operations.get("new_player_alias")
    if new_alias:
        archive.update_one({"_id": MIGRATION + ":aliases:" + str(new_alias["_id"])},
            {"$setOnInsert": {"migration": MIGRATION, "collection": "aliases", "document": None,
                               "created_record_id": new_alias["_id"]}}, upsert=True)
        db.aliases.insert_one(new_alias)
    if operations.get("retired_player") is not None:
        preserve("players", operations["retired_player"])
        db.players.delete_one({"_id": operations["retired_player"]})
    for identity in operations["old_events"]: preserve("events", identity)
    removed = db.events.delete_many({"_id": {"$in": operations["old_events"]}}).deleted_count
    ensure_indexes(db)
    db.repair_runs.update_one({"_id": MIGRATION}, {"$set": {"completed_at": datetime.now(timezone.utc), "events_removed": removed}}, upsert=True)
    return removed


def summary(operations):
    return {"article_updates": len(operations["articles"]), "duplicate_articles_held_as_drafts": operations["duplicates"],
        "story_updates": len(operations["stories"]), "duplicate_stories_archived": sum(bool(v.get("repair_archived")) for v in operations["stories"].values()),
        "historical_article_rewrites_disabled": sum(v.get("rewrite_review_reason") == "historical_content" for v in operations["articles"].values()),
        "duplicate_players_to_merge": int(operations.get("retired_player") is not None),
        "player_reference_updates": {name: len(rows) for name, rows in operations.get("entity_updates", {}).items()},
        "old_queue_events_to_remove": len(operations["old_events"]),
        "queue_cutoff": operations["cutoff"].isoformat(), "already_completed": operations["already_completed"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--restore-check", type=Path)
    args = parser.parse_args()
    if args.apply:
        if not args.restore_check or not args.restore_check.is_file(): parser.error("A successful, local restore-check.json is required")
        check = json.loads(args.restore_check.read_text())
        if not check.get("archive_sha256") or not check.get("collections", {}).get("articles"):
            parser.error("Restore check has no verified article collection")
    database_name = os.environ.get("DB_NAME", "transfernews_db")
    if database_name != "transfernews_db": parser.error("This migration is scoped to transfernews_db")
    database = MongoClient(os.environ["MONGO_URL"])[database_name]
    operations = plan(database, datetime.now(timezone.utc))
    result = summary(operations)
    if args.apply: result["events_removed"] = apply(database, operations)
    result["applied"] = args.apply
    print(json.dumps(result, indent=2))
