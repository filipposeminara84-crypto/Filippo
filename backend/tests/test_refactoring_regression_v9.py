"""
Shopply Backend Refactoring Regression Tests - Iteration 9
Tests all endpoints after monolithic server.py was split into modules:
- database.py, models.py, dependencies.py
- routes/: auth, referral, supermercati, liste, famiglia, notifiche, ottimizza, scraper_routes, seed

Test user: fuzzy@test.com / Test1234!
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ============== FIXTURES ==============

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for test user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "fuzzy@test.com",
        "password": "Test1234!"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ============== HEALTH & ROOT ==============

class TestHealthEndpoints:
    """Test health and root endpoints"""
    
    def test_health_endpoint(self, api_client):
        """GET /api/health returns healthy status"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print(f"✅ Health check passed: {data}")
    
    def test_root_endpoint(self, api_client):
        """GET /api/ returns API info"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "Shopply API" in data.get("message", "")
        assert data.get("status") == "online"
        print(f"✅ Root endpoint: {data}")


# ============== AUTH ENDPOINTS ==============

class TestAuthEndpoints:
    """Test authentication endpoints from routes/auth.py"""
    
    def test_login_success(self, api_client):
        """POST /api/auth/login with valid credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fuzzy@test.com",
            "password": "Test1234!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "fuzzy@test.com"
        print(f"✅ Login success: token received, user={data['user']['nome']}")
    
    def test_login_invalid_credentials(self, api_client):
        """POST /api/auth/login with invalid credentials returns 401"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("✅ Login with invalid credentials correctly returns 401")
    
    def test_get_me_authenticated(self, authenticated_client):
        """GET /api/auth/me returns current user info"""
        response = authenticated_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "fuzzy@test.com"
        assert "id" in data
        assert "preferenze" in data
        assert "statistiche" in data
        print(f"✅ GET /api/auth/me: user={data['nome']}, referral_code={data.get('referral_code')}")
    
    def test_get_me_unauthenticated(self, api_client):
        """GET /api/auth/me without token returns 401/403"""
        # Use a fresh session without auth
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]
        print("✅ GET /api/auth/me without auth correctly returns 401/403")
    
    def test_forgot_password(self, api_client):
        """POST /api/auth/forgot-password returns success message"""
        response = api_client.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "fuzzy@test.com"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Demo mode returns token for testing
        assert "demo_token" in data or "message" in data
        print(f"✅ Forgot password: {data.get('message')}")
    
    def test_register_duplicate_email(self, api_client):
        """POST /api/auth/register with existing email returns 400"""
        response = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "email": "fuzzy@test.com",
            "nome": "Test User",
            "password": "Test1234!"
        })
        assert response.status_code == 400
        data = response.json()
        assert "già registrata" in data.get("detail", "").lower() or "already" in data.get("detail", "").lower()
        print("✅ Register with duplicate email correctly returns 400")


# ============== SUPERMERCATI ENDPOINTS ==============

class TestSupermercatiEndpoints:
    """Test supermarket endpoints from routes/supermercati.py"""
    
    def test_get_supermercati(self, api_client):
        """GET /api/supermercati returns 33 stores"""
        response = api_client.get(f"{BASE_URL}/api/supermercati")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 33
        # Verify structure
        store = data[0]
        assert "id" in store
        assert "nome" in store
        assert "catena" in store
        assert "lat" in store
        assert "lng" in store
        print(f"✅ GET /api/supermercati: {len(data)} stores returned")
    
    def test_get_supermercati_nearby_pioltello(self, api_client):
        """GET /api/supermercati/nearby for Pioltello area"""
        # Pioltello coordinates
        response = api_client.get(f"{BASE_URL}/api/supermercati/nearby", params={
            "lat": 45.4975,
            "lng": 9.3306,
            "raggio_km": 5
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Should include Pioltello stores
        store_names = [s["nome"] for s in data]
        assert any("Pioltello" in name or "Segrate" in name or "Cernusco" in name for name in store_names)
        print(f"✅ GET /api/supermercati/nearby (Pioltello): {len(data)} stores within 5km")
    
    def test_get_supermercato_by_id(self, api_client):
        """GET /api/supermercati/{id} returns specific store"""
        response = api_client.get(f"{BASE_URL}/api/supermercati/coop-pioltello")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "coop-pioltello"
        assert data["catena"] == "Coop"
        print(f"✅ GET /api/supermercati/coop-pioltello: {data['nome']}")
    
    def test_get_supermercato_not_found(self, api_client):
        """GET /api/supermercati/{id} with invalid ID returns 404"""
        response = api_client.get(f"{BASE_URL}/api/supermercati/nonexistent-store")
        assert response.status_code == 404
        print("✅ GET /api/supermercati/nonexistent returns 404")
    
    def test_get_copertura(self, api_client):
        """GET /api/copertura returns coverage data"""
        response = api_client.get(f"{BASE_URL}/api/copertura")
        assert response.status_code == 200
        data = response.json()
        assert "zone_coperte" in data
        assert "totale_negozi" in data
        assert "regioni" in data
        # Should have Lombardia and Sicilia
        assert "Lombardia" in data["regioni"]
        assert "Sicilia" in data["regioni"]
        print(f"✅ GET /api/copertura: {data['totale_negozi']} stores, regions={data['regioni']}")


# ============== PRODOTTI ENDPOINTS ==============

class TestProdottiEndpoints:
    """Test product endpoints from routes/supermercati.py"""
    
    def test_get_prodotti(self, api_client):
        """GET /api/prodotti returns products"""
        response = api_client.get(f"{BASE_URL}/api/prodotti", params={"limit": 50})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Verify structure
        product = data[0]
        assert "id" in product
        assert "nome_prodotto" in product
        assert "prezzo" in product
        assert "categoria" in product
        print(f"✅ GET /api/prodotti: {len(data)} products returned")
    
    def test_get_prodotti_by_categoria(self, api_client):
        """GET /api/prodotti with categoria filter"""
        response = api_client.get(f"{BASE_URL}/api/prodotti", params={
            "categoria": "Latticini",
            "limit": 50
        })
        assert response.status_code == 200
        data = response.json()
        assert all(p["categoria"] == "Latticini" for p in data)
        print(f"✅ GET /api/prodotti?categoria=Latticini: {len(data)} products")
    
    def test_get_prodotti_search(self, api_client):
        """GET /api/prodotti with search filter"""
        response = api_client.get(f"{BASE_URL}/api/prodotti", params={
            "search": "latte",
            "limit": 50
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all("latte" in p["nome_prodotto"].lower() for p in data)
        print(f"✅ GET /api/prodotti?search=latte: {len(data)} products")
    
    def test_get_categorie(self, api_client):
        """GET /api/categorie returns 12 categories"""
        response = api_client.get(f"{BASE_URL}/api/categorie")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 12
        assert "Latticini" in data
        assert "Bevande" in data
        print(f"✅ GET /api/categorie: {len(data)} categories")
    
    def test_autocomplete_prodotti(self, api_client):
        """GET /api/prodotti/autocomplete returns suggestions"""
        response = api_client.get(f"{BASE_URL}/api/prodotti/autocomplete", params={"q": "past"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("past" in name.lower() for name in data)
        print(f"✅ GET /api/prodotti/autocomplete?q=past: {len(data)} suggestions")
    
    def test_get_offerte(self, api_client):
        """GET /api/prodotti/offerte returns offers grouped by store"""
        response = api_client.get(f"{BASE_URL}/api/prodotti/offerte")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should have store IDs as keys
        print(f"✅ GET /api/prodotti/offerte: {len(data)} stores with offers")


# ============== OTTIMIZZA ENDPOINTS ==============

class TestOttimizzaEndpoints:
    """Test optimization endpoints from routes/ottimizza.py"""
    
    def test_ottimizza_basic(self, authenticated_client):
        """POST /api/ottimizza with basic product list"""
        response = authenticated_client.post(f"{BASE_URL}/api/ottimizza", json={
            "lista_prodotti": ["Latte Intero", "Pasta Spaghetti", "Mozzarella"],
            "lat_utente": 45.4975,
            "lng_utente": 9.3306,
            "raggio_km": 10,
            "max_supermercati": 3
        })
        assert response.status_code == 200
        data = response.json()
        assert "piano_ottimale" in data
        assert "costo_totale" in data
        assert "tempo_stimato_min" in data
        assert "risparmio_euro" in data
        assert "num_supermercati" in data
        assert len(data["piano_ottimale"]) > 0
        print(f"✅ POST /api/ottimizza: {data['num_supermercati']} stores, cost={data['costo_totale']}€")
    
    def test_ottimizza_fuzzy_matching(self, authenticated_client):
        """POST /api/ottimizza with quantity suffixes (fuzzy matching)"""
        response = authenticated_client.post(f"{BASE_URL}/api/ottimizza", json={
            "lista_prodotti": ["Olio Extravergine 1L", "Pasta Penne 500g", "Mozzarella 250g"],
            "lat_utente": 45.4975,
            "lng_utente": 9.3306,
            "raggio_km": 10,
            "max_supermercati": 3
        })
        assert response.status_code == 200
        data = response.json()
        # Should find products despite quantity suffixes
        found_count = len(data["lista_prodotti"]) - len(data.get("prodotti_non_trovati", [])) if "lista_prodotti" in data else 3 - len(data.get("prodotti_non_trovati", []))
        assert len(data.get("prodotti_non_trovati", [])) < 3, "Fuzzy matching should find most products"
        print(f"✅ POST /api/ottimizza (fuzzy): found products, not_found={data.get('prodotti_non_trovati', [])}")
    
    def test_ottimizza_location_filtering(self, authenticated_client):
        """POST /api/ottimizza returns stores in specified area"""
        # Pioltello area
        response = authenticated_client.post(f"{BASE_URL}/api/ottimizza", json={
            "lista_prodotti": ["Latte Intero"],
            "lat_utente": 45.4975,
            "lng_utente": 9.3306,
            "raggio_km": 5,
            "max_supermercati": 3
        })
        assert response.status_code == 200
        data = response.json()
        # Stores should be in Lombardia area
        for stop in data["piano_ottimale"]:
            store = stop["supermercato"]
            assert store["regione"] == "Lombardia"
        print(f"✅ POST /api/ottimizza (Pioltello): all stores in Lombardia")
    
    def test_ottimizza_unknown_product(self, authenticated_client):
        """POST /api/ottimizza with unknown product returns it in prodotti_non_trovati"""
        response = authenticated_client.post(f"{BASE_URL}/api/ottimizza", json={
            "lista_prodotti": ["ProdottoInesistenteXYZ123"],
            "lat_utente": 45.4975,
            "lng_utente": 9.3306,
            "raggio_km": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert "ProdottoInesistenteXYZ123" in data.get("prodotti_non_trovati", [])
        print(f"✅ POST /api/ottimizza: unknown product in prodotti_non_trovati")
    
    def test_matrice_prezzi(self, api_client):
        """POST /api/matrice-prezzi returns price matrix"""
        response = api_client.post(f"{BASE_URL}/api/matrice-prezzi", json=["Latte Intero", "Pasta Spaghetti"])
        assert response.status_code == 200
        data = response.json()
        assert "Latte Intero" in data or "latte intero" in str(data).lower()
        print(f"✅ POST /api/matrice-prezzi: {len(data)} products in matrix")
    
    def test_get_storico(self, authenticated_client):
        """GET /api/storico returns search history"""
        response = authenticated_client.get(f"{BASE_URL}/api/storico")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ GET /api/storico: {len(data)} historical searches")


# ============== LISTE ENDPOINTS ==============

class TestListeEndpoints:
    """Test shopping list endpoints from routes/liste.py"""
    
    def test_create_and_get_lista(self, authenticated_client):
        """POST /api/liste creates list, GET /api/liste retrieves it"""
        unique_name = f"TEST_Lista_{uuid.uuid4().hex[:8]}"
        
        # Create
        create_response = authenticated_client.post(f"{BASE_URL}/api/liste", json={
            "nome": unique_name,
            "prodotti": ["Latte", "Pane", "Uova"]
        })
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["nome"] == unique_name
        assert "id" in created
        lista_id = created["id"]
        
        # Get
        get_response = authenticated_client.get(f"{BASE_URL}/api/liste")
        assert get_response.status_code == 200
        lists = get_response.json()
        assert any(l["id"] == lista_id for l in lists)
        
        # Cleanup - delete
        del_response = authenticated_client.delete(f"{BASE_URL}/api/liste/{lista_id}")
        assert del_response.status_code == 200
        
        print(f"✅ POST/GET/DELETE /api/liste: created, retrieved, deleted '{unique_name}'")


# ============== NOTIFICHE ENDPOINTS ==============

class TestNotificheEndpoints:
    """Test notification endpoints from routes/notifiche.py"""
    
    def test_get_notifiche(self, authenticated_client):
        """GET /api/notifiche returns user notifications"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifiche")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ GET /api/notifiche: {len(data)} notifications")
    
    def test_get_notifiche_non_lette(self, authenticated_client):
        """GET /api/notifiche/non-lette returns unread count"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifiche/non-lette")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        print(f"✅ GET /api/notifiche/non-lette: {data['count']} unread")


# ============== REFERRAL ENDPOINTS ==============

class TestReferralEndpoints:
    """Test referral endpoints from routes/referral.py"""
    
    def test_get_referral_stats(self, authenticated_client):
        """GET /api/referral/stats returns referral statistics"""
        response = authenticated_client.get(f"{BASE_URL}/api/referral/stats")
        assert response.status_code == 200
        data = response.json()
        assert "referral_code" in data
        assert "punti_totali" in data
        assert "inviti_completati" in data
        assert "bonus_disponibile" in data
        print(f"✅ GET /api/referral/stats: code={data['referral_code']}, points={data['punti_totali']}")
    
    def test_get_referral_inviti(self, authenticated_client):
        """GET /api/referral/inviti returns invite list"""
        response = authenticated_client.get(f"{BASE_URL}/api/referral/inviti")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ GET /api/referral/inviti: {len(data)} invites")
    
    def test_get_classifica_referral(self, authenticated_client):
        """GET /api/referral/classifica returns leaderboard"""
        response = authenticated_client.get(f"{BASE_URL}/api/referral/classifica")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ GET /api/referral/classifica: {len(data)} users in leaderboard")


# ============== SCRAPER ENDPOINTS ==============

class TestScraperEndpoints:
    """Test scraper endpoints from routes/scraper_routes.py"""
    
    def test_get_scraper_categories(self, authenticated_client):
        """GET /api/scraper/categories returns available sources"""
        response = authenticated_client.get(f"{BASE_URL}/api/scraper/categories")
        assert response.status_code == 200
        data = response.json()
        assert "fonti_disponibili" in data
        assert "categorie" in data
        # Should have 3 sources: doveconviene, pepesto, cross_reference
        assert len(data["fonti_disponibili"]) == 3
        assert "doveconviene" in data["fonti_disponibili"]
        print(f"✅ GET /api/scraper/categories: sources={data['fonti_disponibili']}")
    
    def test_scraper_search_preview(self, authenticated_client):
        """POST /api/scraper/search-preview returns real results"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/scraper/search-preview",
            params={"search_term": "latte"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "search_term" in data
        assert "risultati_totali" in data
        # DoveConviene should return results
        print(f"✅ POST /api/scraper/search-preview: {data['risultati_totali']} results for 'latte'")
    
    def test_get_scraper_status(self, authenticated_client):
        """GET /api/scraper/status returns scraping status"""
        response = authenticated_client.get(f"{BASE_URL}/api/scraper/status")
        assert response.status_code == 200
        data = response.json()
        assert "in_corso" in data
        print(f"✅ GET /api/scraper/status: in_corso={data['in_corso']}")


# ============== FAMIGLIA ENDPOINTS ==============

class TestFamigliaEndpoints:
    """Test family endpoints from routes/famiglia.py"""
    
    def test_get_famiglia(self, authenticated_client):
        """GET /api/famiglia returns family info or null"""
        response = authenticated_client.get(f"{BASE_URL}/api/famiglia")
        assert response.status_code == 200
        # Can be null if user not in a family
        print(f"✅ GET /api/famiglia: response received")
    
    def test_get_inviti_famiglia(self, authenticated_client):
        """GET /api/famiglia/inviti returns pending invites"""
        response = authenticated_client.get(f"{BASE_URL}/api/famiglia/inviti")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ GET /api/famiglia/inviti: {len(data)} pending invites")


# ============== PREFERENZE ENDPOINTS ==============

class TestPreferenzeEndpoints:
    """Test preferences endpoints from routes/supermercati.py"""
    
    def test_get_preferenze(self, authenticated_client):
        """GET /api/preferenze returns user preferences"""
        response = authenticated_client.get(f"{BASE_URL}/api/preferenze")
        assert response.status_code == 200
        data = response.json()
        assert "raggio_max_km" in data
        assert "max_supermercati" in data
        assert "peso_prezzo" in data
        print(f"✅ GET /api/preferenze: raggio={data['raggio_max_km']}km, max_stores={data['max_supermercati']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
