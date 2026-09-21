"""Canonical placements and real ASGI filtering, with an in-memory Mongo substitute."""
import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import mongomock
import pytest

from test_security_regressions import app_module, headers, request
from ad_slot_defaults import DEFAULT_PLACEMENTS, default_ad_slots, ensure_default_ad_slots
from models import AdSlot


class Cursor:
    def __init__(self, raw): self.raw = raw
    def sort(self, *args): self.raw.sort(*args); return self
    async def to_list(self, length): return list(self.raw)[:length]


class Collection:
    def __init__(self, raw): self.raw = raw
    def find(self, *args, **kwargs): return Cursor(self.raw.find(*args, **kwargs))
    async def find_one(self, *args, **kwargs): return self.raw.find_one(*args, **kwargs)
    async def update_one(self, *args, **kwargs):
        await asyncio.sleep(0)
        return self.raw.update_one(*args, **kwargs)


def database():
    raw = mongomock.MongoClient().ad_slot_tests
    return SimpleNamespace(ad_slots=Collection(raw.ad_slots), users=Collection(raw.users))


def test_canonical_default_keys_use_managed_formats_without_custom_code():
    expected = {"top_banner_above_header": 1, "below_header": 31, "sidebar_top": 3,
                "sidebar_middle": 2, "sidebar_bottom": 19, "footer_top": 28, "skyscraper": 4, "global": 6}
    documents = default_ad_slots()
    assert {doc["slot_key"] for doc in documents} == set(expected)
    assert {placement[0]: placement[2] for placement in DEFAULT_PLACEMENTS} == expected
    assert len({doc["id"] for doc in documents}) == 8
    for doc in documents:
        assert not any(doc.get(field) for field in ("html_code", "js_code", "embed_code"))
        assert doc["device_type"] == ("desktop" if doc["slot_key"] in {"skyscraper", "sidebar_top"} else "all")
    assert next(doc for doc in documents if doc["slot_key"] == "skyscraper")["name"] == "Skyscraper (120x600)"
    assert not any(doc["slot_key"] == "mobile_sticky_bottom" for doc in documents)


def test_repeated_and_concurrent_initialization_preserves_every_existing_field():
    db = database()
    custom = deepcopy(default_ad_slots()[0])
    custom.update(id="existing-custom", _id="legacy-object", is_active=False,
                  embed_code="<div>Custom campaign</div>", html_code="<p>Custom HTML</p>",
                  js_code="window.customPlacement=true", device_type="mobile", priority=123,
                  notes="Keep this setting", updated_at="2020-01-01T00:00:00Z")
    db.ad_slots.raw.insert_one(custom)

    async def run():
        results = await asyncio.gather(ensure_default_ad_slots(db), ensure_default_ad_slots(db))
        assert sum(result["created"] for result in results) == 7
        assert await ensure_default_ad_slots(db) == {"created": 0, "updated": 0, "total": 8}
    asyncio.run(run())
    assert db.ad_slots.raw.count_documents({}) == 8
    assert db.ad_slots.raw.find_one({"slot_key": custom["slot_key"]}) == custom
    assert len({doc["slot_key"] for doc in db.ad_slots.raw.find({})}) == 8


def test_six_existing_empty_inline_placements_only_gain_the_two_missing_defaults():
    db = database()
    existing = [doc for doc in default_ad_slots() if doc["slot_key"] not in {"skyscraper", "global"}]
    for doc in existing:
        doc["embed_code"] = None
    db.ad_slots.raw.insert_many(deepcopy(existing))
    result = asyncio.run(ensure_default_ad_slots(db))
    assert result == {"created": 2, "updated": 0, "total": 8}
    for doc in existing:
        assert db.ad_slots.raw.find_one({"slot_key": doc["slot_key"]}) == doc
    assert {doc["slot_key"] for doc in db.ad_slots.raw.find({})} - {doc["slot_key"] for doc in existing} == {"skyscraper", "global"}
    assert db.ad_slots.raw.count_documents({"embed_code": {"$ne": None}}) == 0


@pytest.fixture
def ads_app(app_module, monkeypatch):
    db = database()
    db.users.raw.insert_one(dict(id="admin", email="admin@example.test", name="Fixture admin", role="admin", is_active=True))
    monkeypatch.setattr(app_module, "db", db)
    return app_module


def test_startup_adds_only_missing_slots_without_starting_scheduler(ads_app, monkeypatch):
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    forbidden = Mock(side_effect=AssertionError("Scheduler must not run"))
    monkeypatch.setattr(ads_app, "start_scheduler", forbidden)
    monkeypatch.setattr(ads_app, "init_scheduler_db", forbidden)
    asyncio.run(ads_app.startup_event())
    before = list(ads_app.db.ad_slots.raw.find({}))
    asyncio.run(ads_app.startup_event())
    assert len(before) == 8
    assert list(ads_app.db.ad_slots.raw.find({})) == before
    forbidden.assert_not_called()


def test_admin_init_uses_the_same_keys_and_preserves_disabled_slots(ads_app):
    first = request(ads_app, "POST", "/api/init/ad-slots", headers=headers(ads_app))
    assert first.status_code == 200 and first.json()["created"] == 8
    ads_app.db.ad_slots.raw.update_one({"slot_key": "global"}, {"$set": {"is_active": False, "embed_code": "custom"}})
    again = request(ads_app, "POST", "/api/init/ad-slots", headers=headers(ads_app))
    assert again.status_code == 200 and again.json()["created"] == 0
    assert ads_app.db.ad_slots.raw.count_documents({}) == 8
    assert ads_app.db.ad_slots.raw.find_one({"slot_key": "global"})["is_active"] is False
    assert ads_app.db.ad_slots.raw.find_one({"slot_key": "global"})["embed_code"] == "custom"
    assert request(ads_app, "POST", "/api/init/ad-slots").status_code == 401


@pytest.mark.parametrize("params,expected", [
    ({"page_type": "news_detail", "device_type": "desktop"}, {"both", "all_page", "all_device", "all"}),
    ({"page_type": "news_detail", "device_type": "mobile"}, {"wrong_device", "all_device", "all"}),
    ({"page_type": "homepage", "device_type": "desktop"}, {"wrong_page", "all_page", "all"}),
])
def test_active_endpoint_requires_page_and_device_to_match(ads_app, params, expected):
    for key, page, device, active in [
        ("both", "news_detail", "desktop", True), ("wrong_page", "homepage", "desktop", True),
        ("wrong_device", "news_detail", "mobile", True), ("all_page", "all", "desktop", True),
        ("all_device", "news_detail", "all", True), ("all", "all", "all", True),
        ("disabled", "all", "all", False),
    ]:
        ads_app.db.ad_slots.raw.insert_one(AdSlot(name=key, slot_key=key, position="test", page_type=page,
            device_type=device, is_active=active).model_dump(mode="json"))
    response = request(ads_app, "GET", "/api/ad-slots/active", params=params)
    assert response.status_code == 200
    assert {slot["slot_key"] for slot in response.json()} == expected
