"""
Test P0 Fixes - Iteration 8
1. Fuzzy Matching in Optimization Algorithm
2. Multi-Source Scraping System (DoveConviene, Pepesto, Cross-Reference)

Tests verify:
- Products with quantity suffixes (1L, 500g, 250g) match DB products without them
- Exact matches still work
- Unknown products return in prodotti_non_trovati
- Location-based filtering works
- Scraper categories return fonti_disponibili
- Search preview returns results with fonte field
- Scraper run triggers without error
- Price matrix uses fuzzy matching
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "fuzzy@test.com"
TEST_PASSWORD = "Test1234!"

# Pioltello coordinates (Lombardia)
PIOLTELLO_LAT = 45.4975
PIOLTELLO_LNG = 9.3306

# Catania coordinates (Sicilia)
CATANIA_LAT = 37.5079
CATANIA_LNG = 15.0830


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    # Try login first
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if login_resp.status_code == 200:
        return login_resp.json()["access_token"]
    
    # If login fails, register the user
    register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "nome": "Fuzzy Test User"
    })
    
    if register_resp.status_code == 200:
        return register_resp.json()["access_token"]
    
    # If registration fails (user exists but wrong password), skip tests
    pytest.skip(f"Could not authenticate: {login_resp.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestFuzzyMatchingOptimization:
    """Test fuzzy matching in /api/ottimizza endpoint"""
    
    def test_fuzzy_match_olio_extravergine_1l(self, auth_headers):
        """'Olio Extravergine 1L' should match 'Olio Extravergine' in DB"""
        response = requests.post(f"{BASE_URL}/api/ottimizza", headers=auth_headers, json={
            "lista_prodotti": ["Olio Extravergine 1L"],
            "lat_utente": PIOLTELLO_LAT,
            "lng_utente": PIOLTELLO_LNG,
            "raggio_km": 10,
            "max_supermercati": 3
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "piano_ottimale" in data, "Response should have piano_ottimale"
        assert "prodotti_non_trovati" in data, "Response should have prodotti_non_trovati"
        
        # Product should be found (not in prodotti_non_trovati)
        assert "Olio Extravergine 1L" not in data["prodotti_non_trovati"], \
            f"'Olio Extravergine 1L' should be matched via fuzzy matching, but was in prodotti_non_trovati: {data['prodotti_non_trovati']}"
        
        # Should have at least one store in the plan
        assert len(data["piano_ottimale"]) > 0, "Should have at least one store in plan"
        
        # Verify the product is assigned to a store
        all_products = []
        for store in data["piano_ottimale"]:
            for prod in store["prodotti"]:
                all_products.append(prod["prodotto"])
        
        assert "Olio Extravergine 1L" in all_products, \
            f"'Olio Extravergine 1L' should be in assigned products: {all_products}"
    
    def test_fuzzy_match_pasta_penne_500g(self, auth_headers):
        """'Pasta Penne 500g' should match 'Pasta Penne' in DB"""
        response = requests.post(f"{BASE_URL}/api/ottimizza", headers=auth_headers, json={
            "lista_prodotti": ["Pasta Penne 500g"],
            "lat_utente": PIOLTELLO_LAT,
            "lng_utente": PIOLTELLO_LNG,
            "raggio_km": 10,
            "max_supermercati": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Product should be found
        assert "Pasta Penne 500g" not in data["prodotti_non_trovati"], \
            f"'Pasta Penne 500g' should be matched via fuzzy matching"
    
    def test_fuzzy_match_mozzarella_250g(self, auth_headers):
        """'Mozzarella 250g' should match 'Mozzarella' in DB"""
        response = requests.post(f"{BASE_URL}/api/ottimizza", headers=auth_headers, json={
            "lista_prodotti": ["Mozzarella 250g"],
            "lat_utente": PIOLTELLO_LAT,
            "lng_utente": PIOLTELLO_LNG,
            "raggio_km": 10,
            "max_supermercati": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Product should be found
        assert "Mozzarella 250g" not in data["prodotti_non_trovati"], \
            f"'Mozzarella 250g' should be matched via fuzzy matching"
    
    def test_exact_match_latte_intero(self, auth_headers):
        """Exact match still works - 'Latte Intero' matches 'Latte Intero 1L' in DB"""
        response = requests.post(f"{BASE_URL}/api/ottimizza", headers=auth_headers, json={
            "lista_prodotti": ["Latte Intero"],
            "lat_utente": PIOLTELLO_LAT,
            "lng_utente": PIOLTELLO_LNG,
            "raggio_km": 10,
            "max_supermercati": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Product should be found
        assert "Latte Intero" not in data["prodotti_non_trovati"], \
            f"'Latte Intero' should match products in DB"
    
    def test_unknown_product_in_non_trovati(self, auth_headers):
        """Unknown product should return in prodotti_non_trovati list"""
        response = requests.post(f"{BASE_URL}/api/ottimizza", headers=auth_headers, json={
            "lista_prodotti": ["ProdottoInesistenteXYZ123"],
            "lat_utente": PIOLTELLO_LAT,
            "lng_utente": PIOLTELLO_LNG,
            "raggio_km": 10,
            "max_supermercati": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Unknown product should be in prodotti_non_trovati
        assert "ProdottoInesistenteXYZ123" in data["prodotti_non_trovati"], \
            f"Unknown product should be in prodotti_non_trovati: {data['prodotti_non_trovati']}"
    
    def test_location_filtering_pioltello(self, auth_headers):
        """Location-based filtering works for Pioltello"""
        response = requests.post(f"{BASE_URL}/api/ottimizza", headers=auth_headers, json={
            "lista_prodotti": ["Latte Intero", "Pasta Barilla"],
            "lat_utente": PIOLTELLO_LAT,
            "lng_utente": PIOLTELLO_LNG,
            "raggio_km": 5,
            "max_supermercati": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have stores in the plan
        assert len(data["piano_ottimale"]) > 0, "Should find stores near Pioltello"
        
        # Verify stores are in Lombardia area (check store names contain Pioltello/Segrate/Cernusco)
        store_names = [s["supermercato"]["nome"] for s in data["piano_ottimale"]]
        lombardia_keywords = ["Pioltello", "Segrate", "Cernusco"]
        has_lombardia_store = any(
            any(kw.lower() in name.lower() for kw in lombardia_keywords)
            for name in store_names
        )
        assert has_lombardia_store, f"Should have Lombardia stores, got: {store_names}"
    
    def test_location_filtering_catania(self, auth_headers):
        """Location-based filtering works for Catania"""
        response = requests.post(f"{BASE_URL}/api/ottimizza", headers=auth_headers, json={
            "lista_prodotti": ["Latte Intero", "Pasta Barilla"],
            "lat_utente": CATANIA_LAT,
            "lng_utente": CATANIA_LNG,
            "raggio_km": 10,
            "max_supermercati": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have stores in the plan
        assert len(data["piano_ottimale"]) > 0, "Should find stores near Catania"
        
        # Verify stores are in Sicilia area
        store_names = [s["supermercato"]["nome"] for s in data["piano_ottimale"]]
        sicilia_keywords = ["Catania", "Palermo"]
        has_sicilia_store = any(
            any(kw.lower() in name.lower() for kw in sicilia_keywords)
            for name in store_names
        )
        assert has_sicilia_store, f"Should have Sicilia stores, got: {store_names}"


class TestMultiSourceScraping:
    """Test multi-source scraping system"""
    
    def test_scraper_categories_returns_fonti_disponibili(self, auth_headers):
        """GET /api/scraper/categories returns fonti_disponibili list"""
        response = requests.get(f"{BASE_URL}/api/scraper/categories", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check fonti_disponibili exists
        assert "fonti_disponibili" in data, "Response should have fonti_disponibili"
        fonti = data["fonti_disponibili"]
        
        # Should include doveconviene, pepesto, cross_reference
        assert "doveconviene" in fonti, f"fonti_disponibili should include 'doveconviene': {fonti}"
        assert "pepesto" in fonti, f"fonti_disponibili should include 'pepesto': {fonti}"
        assert "cross_reference" in fonti, f"fonti_disponibili should include 'cross_reference': {fonti}"
        
        # Should also have categorie
        assert "categorie" in data, "Response should have categorie"
        assert len(data["categorie"]) > 0, "Should have at least one category"
    
    def test_search_preview_doveconviene_latte(self, auth_headers):
        """POST /api/scraper/search-preview: DoveConviene returns results for 'latte'"""
        response = requests.post(
            f"{BASE_URL}/api/scraper/search-preview",
            headers=auth_headers,
            params={"search_term": "latte"},
            json=["doveconviene"]  # Only use doveconviene source
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "search_term" in data, "Response should have search_term"
        assert data["search_term"] == "latte", f"search_term should be 'latte': {data['search_term']}"
        assert "risultati_totali" in data, "Response should have risultati_totali"
        assert "prodotti" in data, "Response should have prodotti"
        
        # Note: DoveConviene scraping may return 0 results if the site is blocking or slow
        # We just verify the structure is correct
        print(f"DoveConviene returned {data['risultati_totali']} results for 'latte'")
    
    def test_search_preview_results_have_fonte_field(self, auth_headers):
        """POST /api/scraper/search-preview: Results include 'fonte' field per product"""
        response = requests.post(
            f"{BASE_URL}/api/scraper/search-preview",
            headers=auth_headers,
            params={"search_term": "pasta"},
            json=["doveconviene"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # If there are products, verify they have fonte field
        if data.get("prodotti") and len(data["prodotti"]) > 0:
            for prod in data["prodotti"][:5]:  # Check first 5
                assert "fonte" in prod, f"Product should have 'fonte' field: {prod}"
                assert prod["fonte"] == "doveconviene", f"fonte should be 'doveconviene': {prod['fonte']}"
        
        # Also check per_fonte breakdown
        if "per_fonte" in data:
            print(f"Results per fonte: {data['per_fonte']}")
    
    def test_scraper_run_triggers_without_error(self, auth_headers):
        """POST /api/scraper/run: Triggers background scraping without error"""
        response = requests.post(
            f"{BASE_URL}/api/scraper/run",
            headers=auth_headers,
            params={"search_term": "yogurt"},
            json=["doveconviene"]
        )
        
        # Should return 200 or 409 (if scraping already in progress)
        assert response.status_code in [200, 409], f"Expected 200 or 409, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data, "Response should have message"
            assert "fonti" in data, "Response should have fonti"
            print(f"Scraper run response: {data}")
    
    def test_scraper_status_returns_status(self, auth_headers):
        """GET /api/scraper/status: Returns scraping status"""
        response = requests.get(f"{BASE_URL}/api/scraper/status", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check status structure
        assert "in_corso" in data, "Response should have in_corso"
        assert isinstance(data["in_corso"], bool), "in_corso should be boolean"
        
        print(f"Scraper status: in_corso={data['in_corso']}")


class TestPriceMatrixFuzzyMatching:
    """Test fuzzy matching in /api/matrice-prezzi endpoint"""
    
    def test_matrice_prezzi_fuzzy_matching(self, auth_headers):
        """POST /api/matrice-prezzi: Fuzzy matching works for price matrix"""
        response = requests.post(
            f"{BASE_URL}/api/matrice-prezzi",
            headers=auth_headers,
            json=["Olio Extravergine 1L", "Pasta Penne 500g", "Latte Intero"]
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check that products are in response
        assert "Olio Extravergine 1L" in data, "Response should have 'Olio Extravergine 1L'"
        assert "Pasta Penne 500g" in data, "Response should have 'Pasta Penne 500g'"
        assert "Latte Intero" in data, "Response should have 'Latte Intero'"
        
        # At least one product should have prices (fuzzy matching should find them)
        has_prices = False
        for prod, prices in data.items():
            if len(prices) > 0:
                has_prices = True
                print(f"{prod}: {len(prices)} stores with prices")
        
        assert has_prices, f"At least one product should have prices via fuzzy matching: {data}"


class TestOptimizationResponseStructure:
    """Test optimization response structure"""
    
    def test_optimization_response_structure(self, auth_headers):
        """Verify optimization response has correct structure"""
        response = requests.post(f"{BASE_URL}/api/ottimizza", headers=auth_headers, json={
            "lista_prodotti": ["Latte Intero", "Pasta Barilla", "Olio Extravergine"],
            "lat_utente": PIOLTELLO_LAT,
            "lng_utente": PIOLTELLO_LNG,
            "raggio_km": 10,
            "max_supermercati": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        required_fields = [
            "piano_ottimale", "costo_totale", "tempo_stimato_min",
            "risparmio_euro", "risparmio_percentuale", "num_supermercati",
            "distanza_totale_km", "prodotti_non_trovati"
        ]
        
        for field in required_fields:
            assert field in data, f"Response should have '{field}'"
        
        # Check piano_ottimale structure
        if len(data["piano_ottimale"]) > 0:
            store = data["piano_ottimale"][0]
            assert "supermercato" in store, "Store should have 'supermercato'"
            assert "prodotti" in store, "Store should have 'prodotti'"
            assert "subtotale" in store, "Store should have 'subtotale'"
            assert "ordine" in store, "Store should have 'ordine'"
            
            # Check product structure
            if len(store["prodotti"]) > 0:
                prod = store["prodotti"][0]
                assert "prodotto" in prod, "Product should have 'prodotto'"
                assert "prezzo" in prod, "Product should have 'prezzo'"
                assert "supermercato_id" in prod, "Product should have 'supermercato_id'"
                assert "supermercato_nome" in prod, "Product should have 'supermercato_nome'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
