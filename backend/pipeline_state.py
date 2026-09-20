"""Persistent pipeline work leases and conservative source freshness rules."""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from uuid import uuid4

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError


def utcnow():
    return datetime.now(timezone.utc)


def parse_source_time(value):
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str) and value.strip():
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                result = parsedate_to_datetime(value)
            except (TypeError, ValueError, OverflowError):
                return None
    else:
        return None
    # MongoDB's default decoder returns naive UTC for stored BSON dates.
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def review_reason(event):
    published = parse_source_time(event.get("source_published_at"))
    if published is None:
        return "missing_source_date"
    age = utcnow() - published
    max_age = max(1, min(168, int(os.environ.get("MAX_AUTO_PUBLISH_AGE_HOURS", "48"))))
    if age < -timedelta(minutes=10):
        return "future_source_date"
    if age > timedelta(hours=max_age):
        return "stale_source"
    return None


def retry_at(attempt):
    return utcnow() + timedelta(seconds=min(3600, 60 * (2 ** min(max(attempt - 1, 0), 6))))


def due_query(field, now):
    return {"$or": [{field: {"$exists": False}}, {field: None}, {field: {"$lte": now}}]}


class StoryBusy(RuntimeError):
    pass


@asynccontextmanager
async def story_lease(db, identity):
    """Serialize story and article updates across API calls and scheduler workers."""
    now, token = utcnow(), uuid4().hex
    query = {"_id": identity, **due_query("expires_at", now)}
    try:
        lock = await db.pipeline_locks.find_one_and_update(
            query, {"$set": {"token": token, "expires_at": now + timedelta(minutes=5)}},
            upsert=True, return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError as exc:
        raise StoryBusy("story_busy") from exc
    if not lock or lock.get("token") != token:
        raise StoryBusy("story_busy")
    try:
        yield
    finally:
        await db.pipeline_locks.delete_one({"_id": identity, "token": token})
