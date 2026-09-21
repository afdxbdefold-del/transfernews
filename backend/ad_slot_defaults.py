"""Canonical ad placements; existing editorial configuration is never overwritten."""
from uuid import NAMESPACE_URL, uuid5

from pymongo.errors import DuplicateKeyError

from models import AdSlot


DEFAULT_PLACEMENTS = (
    ("top_banner_above_header", "Megabanner (728x90)", 1, "header_above", "all", 100),
    ("below_header", "Billboard (970x250)", 31, "below_header", "all", 99),
    ("sidebar_top", "Half Page (300x600)", 3, "sidebar_top", "desktop", 95),
    ("sidebar_middle", "MREC (300x250)", 2, "sidebar_middle", "all", 94),
    ("sidebar_bottom", "MREC 2 (300x250)", 19, "sidebar_bottom", "all", 93),
    ("footer_top", "Above Footer", 28, "footer_top", "all", 90),
    ("skyscraper", "Skyscraper (120x600)", 4, "sidebar_left", "desktop", 98),
    ("global", "Global/Floating", 6, "floating", "all", 85),
)


def default_ad_slots():
    """Frontend owns each canonical format's managed loading and cleanup."""
    documents = []
    for key, name, _format_id, position, device, priority in DEFAULT_PLACEMENTS:
        document = AdSlot(
            id=str(uuid5(NAMESPACE_URL, "transfernews:ad-slot:" + key)),
            name=name, slot_key=key, page_type="all", position=position,
            device_type=device, is_active=True, priority=priority,
        ).model_dump(mode="json")
        document["_id"] = "ad-slot:" + key
        documents.append(document)
    return documents


async def ensure_default_ad_slots(db):
    """Idempotent startup / admin init, preserving disabled slots and custom code."""
    created = 0
    for document in default_ad_slots():
        query = {"slot_key": document["slot_key"]}
        try:
            result = await db.ad_slots.update_one(query, {"$setOnInsert": document}, upsert=True)
            created += int(result.upserted_id is not None)
        except DuplicateKeyError:
            # The deterministic _id prevents duplicate first-start inserts if
            # several workers race; accept only an already existing same key.
            if not await db.ad_slots.find_one(query, {"_id": 1}):
                raise
    return {"created": created, "updated": 0, "total": len(DEFAULT_PLACEMENTS)}
