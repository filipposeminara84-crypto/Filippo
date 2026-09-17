"""Tests for v11: Interactive Store Map + Enhanced DoveConviene scraping."""
import os
import requests
import pytest

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Pioltello coords (already discovered: 40 stores)
LAT, LNG = 45.4975, 9.3306


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth_token(api):
    # heavy_buyer should already exist; if not, seed
    r = api.post(f"{BASE_URL}/api/auth/login", json={
        "email": "heavy_buyer@test.com", "password": "test1234"})
    if r.status_code != 200:
        api.post(f"{BASE_URL}/api/acquisti/seed-mock")
        r = api.post(f"{BASE_URL}/api/auth/login", json={
            "email": "heavy_buyer@test.com", "password": "test1234"})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json().get("access_token") or r.json().get("token")


# ======== DISCOVER ========
def test_discover_returns_osm_stores(api):
    r = api.post(f"{BASE_URL}/api/supermercati/discover",
                 params={"lat": LAT, "lng": LNG, "raggio_km": 5})
    assert r.status_code == 200
    data = r.json()
    assert "supermercati" in data
    assert data["stores"] > 0, "Expected discovered/cached stores at Pioltello"
    # Must include lat/lng for map rendering
    s0 = data["supermercati"][0]
    assert "lat" in s0 and "lng" in s0
    assert "catena" in s0
    assert "id" in s0 and s0["id"].startswith("osm-")


# ======== NEARBY (only OSM when available) ========
def test_nearby_returns_only_osm(api):
    r = api.get(f"{BASE_URL}/api/supermercati/nearby",
                params={"lat": LAT, "lng": LNG, "raggio_km": 5})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # all returned must have fonte=osm (since OSM stores exist in area)
    for s in data:
        assert s.get("fonte") == "osm", f"Non-OSM store leaked: {s}"
    # sorted by distance ascending
    distances = [s["distanza_km"] for s in data]
    assert distances == sorted(distances)


# ======== SCRAPE-OFFERTE manual trigger ========
def test_scrape_offerte_endpoint(api):
    r = api.post(f"{BASE_URL}/api/supermercati/scrape-offerte",
                 params={"lat": LAT, "lng": LNG, "raggio_km": 5})
    assert r.status_code == 200
    data = r.json()
    # Should return chains list and stores count when nearby exists
    assert "stores" in data, f"Unexpected response: {data}"
    assert data["stores"] > 0
    assert "chains" in data
    assert isinstance(data["chains"], list)
    assert len(data["chains"]) >= 1
    assert "message" in data


def test_scrape_offerte_no_stores_in_area(api):
    # Middle of Sahara - should return "no stores" message
    r = api.post(f"{BASE_URL}/api/supermercati/scrape-offerte",
                 params={"lat": 23.0, "lng": 13.0, "raggio_km": 5})
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert "Nessun negozio" in data["message"] or data.get("stores", 0) == 0


# ======== Personalized offers w/ OSM stores ========
def test_personalized_offers_use_osm_stores(api, auth_token):
    h = {"Authorization": f"Bearer {auth_token}"}
    r = api.get(f"{BASE_URL}/api/offerte/personalizzate",
                params={"lat": LAT, "lng": LNG, "raggio_km": 15}, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "offers" in data
    if len(data["offers"]) == 0:
        pytest.skip("No personalized offers — likely no scraped offers yet")
    osm_offers = [o for o in data["offers"] if o.get("supermarketId", "").startswith("osm-")]
    # Most/all offers in Pioltello should be osm-
    assert len(osm_offers) > 0, "No osm- supermarketId found in personalized offers"
