"""Tests for Top-Deals API and club squad endpoints (iteration 10)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://deploy-transfers.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# --- Top-Deals ---
class TestTopDeals:
    def test_top_deals_endpoint(self, client):
        r = client.get(f"{BASE_URL}/api/transfers/top-deals")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 10

    def test_top_deals_sorted_desc(self, client):
        r = client.get(f"{BASE_URL}/api/transfers/top-deals")
        data = r.json()
        fees = [t["fee_amount"] for t in data]
        assert fees == sorted(fees, reverse=True), "Top-deals must be sorted by fee_amount descending"

    def test_top_deals_top_entries(self, client):
        r = client.get(f"{BASE_URL}/api/transfers/top-deals")
        data = r.json()
        top3 = [(t["player_name"], t["fee_amount"]) for t in data[:3]]
        assert top3[0] == ("Enzo Fernández", 121000000)
        assert top3[1] == ("Declan Rice", 116000000)
        assert top3[2] == ("Moisés Caicedo", 115000000)

    def test_top_deals_fields(self, client):
        r = client.get(f"{BASE_URL}/api/transfers/top-deals")
        for t in r.json()[:5]:
            for k in ("player_name", "from_club", "to_club", "fee_amount", "fee"):
                assert k in t and t[k] is not None


# --- Club squads ---
CLUBS = [
    ("liverpool", 18, ["Mohamed Salah", "Virgil van Dijk", "Alisson", "Darwin Núñez"]),
    ("arsenal", 18, ["Bukayo Saka", "Declan Rice", "Martin Ødegaard", "Kai Havertz"]),
    ("chelsea", 18, ["Cole Palmer", "Enzo Fernández", "Moisés Caicedo", "Nicolas Jackson"]),
    ("barcelona", 18, ["Pedri", "Robert Lewandowski", "Lamine Yamal", "Marc-André ter Stegen"]),
]


@pytest.mark.parametrize("slug,min_players,expected_names", CLUBS)
def test_club_squad(client, slug, min_players, expected_names):
    r = client.get(f"{BASE_URL}/api/clubs/slug/{slug}")
    assert r.status_code == 200, f"Club {slug} not found"
    club_id = r.json()["id"]

    r = client.get(f"{BASE_URL}/api/players", params={"current_club_id": club_id, "limit": 50})
    assert r.status_code == 200
    players = r.json()
    assert len(players) >= min_players, f"{slug} has only {len(players)} players"

    # All players have market_value
    mv_count = sum(1 for p in players if p.get("market_value"))
    assert mv_count >= min_players, f"{slug} has only {mv_count} players with market_value"

    names = [p["name"] for p in players]
    for expected in expected_names:
        assert expected in names, f"{slug}: expected player {expected} not found in {names}"


def test_squad_has_wikimedia_images(client):
    total_with_img = 0
    for slug, _, _ in CLUBS:
        cr = client.get(f"{BASE_URL}/api/clubs/slug/{slug}")
        cid = cr.json()["id"]
        players = client.get(f"{BASE_URL}/api/players", params={"current_club_id": cid, "limit": 50}).json()
        with_img = sum(1 for p in players if p.get("image") and "wikimedia" in p.get("image", ""))
        total_with_img += with_img
    assert total_with_img >= 20, f"Only {total_with_img} players have wikimedia images"
