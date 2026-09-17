"""Tests for the personalized recommendation engine and purchase history."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://shopply-grocery.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

LAT, LNG = 45.4975, 9.3306

CREDS = {
    "heavy": ("heavy_buyer@test.com", "test1234"),
    "discount": ("discount_hunter@test.com", "test1234"),
    "new": ("new_user@test.com", "test1234"),
}


@pytest.fixture(scope="session")
def seed_users():
    """Seed the 3 mock users with purchase histories."""
    r = requests.post(f"{API}/acquisti/seed-mock", timeout=60)
    assert r.status_code == 200, f"Seed failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    assert "users" in data
    assert len(data["users"]) == 3
    return data


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"Login failed for {email}: {r.text[:200]}"
    token = r.json().get("token") or r.json().get("access_token")
    assert token, f"No token returned for {email}"
    return token


@pytest.fixture(scope="session")
def tokens(seed_users):
    return {k: _login(*v) for k, v in CREDS.items()}


# ---------- Seed -----------
class TestSeed:
    def test_seed_returns_three_users(self, seed_users):
        u = seed_users["users"]
        assert "heavy_buyer@test.com" in u
        assert "discount_hunter@test.com" in u
        assert "new_user@test.com" in u
        assert u["heavy_buyer@test.com"]["purchases"] >= 15
        assert u["discount_hunter@test.com"]["purchases"] >= 15
        assert u["new_user@test.com"]["purchases"] == 0


# ---------- Personalized Offers -----------
class TestPersonalizedOffers:
    def test_heavy_buyer_personalized(self, tokens):
        h = {"Authorization": f"Bearer {tokens['heavy']}"}
        r = requests.get(f"{API}/offerte/personalizzate", params={"lat": LAT, "lng": LNG, "debug": "true"}, headers=h, timeout=60)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert "offers" in d and "meta" in d
        assert d["meta"].get("isColdStart") is False, f"Heavy buyer should NOT be cold start: {d['meta']}"
        assert len(d["offers"]) > 0
        # debug=true must include scoreBreakdown
        assert "scoreBreakdown" in d["offers"][0], "debug=true must include scoreBreakdown"
        # Must have profileSummary in meta for non-cold user
        assert "profileSummary" in d["meta"]
        top_cats = [c["name"] for c in d["meta"]["profileSummary"]["topCategories"]]
        # Heavy buyer was seeded with Latticini-heavy
        assert "Latticini" in top_cats, f"Expected Latticini in top cats, got {top_cats}"

    def test_discount_hunter_different_ranking(self, tokens):
        h_h = {"Authorization": f"Bearer {tokens['heavy']}"}
        h_d = {"Authorization": f"Bearer {tokens['discount']}"}
        params = {"lat": LAT, "lng": LNG, "debug": "true"}
        r1 = requests.get(f"{API}/offerte/personalizzate", params=params, headers=h_h, timeout=60).json()
        r2 = requests.get(f"{API}/offerte/personalizzate", params=params, headers=h_d, timeout=60).json()
        ids1 = [o["offerId"] for o in r1["offers"][:10]]
        ids2 = [o["offerId"] for o in r2["offers"][:10]]
        assert ids1 != ids2, "Heavy and discount user top 10 should differ"
        assert r2["meta"].get("isColdStart") is False

    def test_new_user_cold_start(self, tokens):
        h = {"Authorization": f"Bearer {tokens['new']}"}
        r = requests.get(f"{API}/offerte/personalizzate", params={"lat": LAT, "lng": LNG}, headers=h, timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert d["meta"].get("isColdStart") is True, f"New user must be cold start: {d['meta']}"
        assert len(d["offers"]) > 0

    def test_no_geolocation_no_crash(self, tokens):
        h = {"Authorization": f"Bearer {tokens['heavy']}"}
        r = requests.get(f"{API}/offerte/personalizzate", headers=h, timeout=60)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert "offers" in d
        # distance should be None when no lat/lng
        if d["offers"]:
            assert d["offers"][0].get("distanceKm") is None

    def test_debug_false_no_breakdown(self, tokens):
        h = {"Authorization": f"Bearer {tokens['heavy']}"}
        r = requests.get(f"{API}/offerte/personalizzate", params={"lat": LAT, "lng": LNG, "debug": "false"}, headers=h, timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert len(d["offers"]) > 0
        assert "scoreBreakdown" not in d["offers"][0], "scoreBreakdown should NOT be in response when debug=false"

    def test_offers_have_score_and_reason_label(self, tokens):
        h = {"Authorization": f"Bearer {tokens['heavy']}"}
        r = requests.get(f"{API}/offerte/personalizzate", params={"lat": LAT, "lng": LNG}, headers=h, timeout=60)
        d = r.json()
        first = d["offers"][0]
        for k in ("offerId", "productName", "categoryName", "offerPrice", "supermarketName", "score", "reasonLabel"):
            assert k in first, f"Missing key {k}"
        assert isinstance(first["score"], (int, float))


# ---------- Purchase CRUD -----------
class TestPurchaseCRUD:
    def test_record_single_purchase_and_verify(self, tokens):
        h = {"Authorization": f"Bearer {tokens['new']}", "Content-Type": "application/json"}
        payload = {
            "productId": "test_prod_1",
            "productName": "TEST_Latte Intero 1L",
            "categoryName": "Latticini",
            "brand": "TestBrand",
            "quantity": 2,
            "unitPrice": 1.49,
            "supermarketId": "esselunga-pioltello",
            "supermarketName": "Esselunga Pioltello",
        }
        r = requests.post(f"{API}/acquisti", json=payload, headers=h, timeout=30)
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        assert "id" in body

        # Verify retrievable
        r2 = requests.get(f"{API}/acquisti", headers=h, timeout=30)
        assert r2.status_code == 200
        items = r2.json()["purchases"]
        assert any(p["productName"] == "TEST_Latte Intero 1L" for p in items)

    def test_get_purchase_history_heavy(self, tokens):
        h = {"Authorization": f"Bearer {tokens['heavy']}"}
        r = requests.get(f"{API}/acquisti", headers=h, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "purchases" in d
        assert d["total"] > 20

    def test_unauthenticated_personalized_blocked(self):
        r = requests.get(f"{API}/offerte/personalizzate", timeout=30)
        assert r.status_code in (401, 403)
