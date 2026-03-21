"""
Test Suite for Shopply v2.2 Features
- Tests seed endpoint (12 supermarkets, ~2500 products)
- Tests supermercati endpoints
- Tests prodotti endpoints with filters
- Tests scraper endpoints (DoveConviene integration)
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shopply-grocery.preview.emergentagent.com')

# Expected supermarket chains
EXPECTED_CHAINS = ["Coop", "Esselunga", "Lidl", "Eurospin", "Carrefour", "Penny", "MD", "Conad", "Aldi", "Despar", "Unes", "Iperal"]

# Expected categories
EXPECTED_CATEGORIES = [
    "Latticini", "Pane e Cereali", "Frutta e Verdura", "Carne e Pesce",
    "Bevande", "Snack e Dolci", "Condimenti e Salse", "Surgelati",
    "Igiene e Casa", "Igiene Personale", "Baby e Infanzia", "Pet Food"
]


class TestSeedEndpoint:
    """Test POST /api/seed - populates DB with 12 supermarkets and ~2500 products"""
    
    def test_seed_database(self):
        """Seed the database and verify counts"""
        response = requests.post(f"{BASE_URL}/api/seed")
        assert response.status_code == 200, f"Seed failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert data["supermercati"] == 12, f"Expected 12 supermarkets, got {data['supermercati']}"
        assert data["prodotti"] >= 2000, f"Expected 2000+ products, got {data['prodotti']}"
        assert data["categorie"] == 12, f"Expected 12 categories, got {data['categorie']}"
        
        print(f"✅ Seed successful: {data['supermercati']} supermarkets, {data['prodotti']} products, {data['categorie']} categories")


class TestSupermercatiEndpoints:
    """Test GET /api/supermercati - returns all 12 supermarkets"""
    
    def test_get_all_supermercati(self):
        """Get all supermarkets and verify 12 are returned"""
        response = requests.get(f"{BASE_URL}/api/supermercati")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert len(data) == 12, f"Expected 12 supermarkets, got {len(data)}"
        
        # Verify all expected chains are present
        chains = [s["catena"] for s in data]
        for expected_chain in EXPECTED_CHAINS:
            assert expected_chain in chains, f"Missing chain: {expected_chain}"
        
        # Verify structure of first supermarket
        first = data[0]
        assert "id" in first
        assert "nome" in first
        assert "catena" in first
        assert "indirizzo" in first
        assert "lat" in first
        assert "lng" in first
        assert "orari" in first
        assert "servizi" in first
        
        print(f"✅ GET /api/supermercati: {len(data)} supermarkets returned")
        print(f"   Chains: {', '.join(chains)}")
    
    def test_get_supermercato_by_id(self):
        """Get a specific supermarket by ID"""
        # First get all to find an ID
        all_response = requests.get(f"{BASE_URL}/api/supermercati")
        supermercati = all_response.json()
        
        if supermercati:
            test_id = supermercati[0]["id"]
            response = requests.get(f"{BASE_URL}/api/supermercati/{test_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == test_id
            print(f"✅ GET /api/supermercati/{test_id}: {data['nome']}")
    
    def test_get_supermercato_not_found(self):
        """Get non-existent supermarket returns 404"""
        response = requests.get(f"{BASE_URL}/api/supermercati/nonexistent-id")
        assert response.status_code == 404
        print("✅ GET /api/supermercati/nonexistent-id: 404 as expected")


class TestProdottiEndpoints:
    """Test GET /api/prodotti with various filters"""
    
    def test_get_all_prodotti(self):
        """Get products without filters"""
        response = requests.get(f"{BASE_URL}/api/prodotti")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert len(data) > 0, "No products returned"
        
        # Verify structure
        first = data[0]
        assert "id" in first
        assert "nome_prodotto" in first
        assert "categoria" in first
        assert "brand" in first
        assert "prezzo" in first
        assert "supermercato_id" in first
        
        print(f"✅ GET /api/prodotti: {len(data)} products returned")
    
    def test_get_prodotti_by_categoria(self):
        """Get products filtered by category"""
        response = requests.get(f"{BASE_URL}/api/prodotti", params={"categoria": "Latticini"})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "No Latticini products found"
        
        # Verify all returned products are in Latticini category
        for prod in data:
            assert prod["categoria"] == "Latticini", f"Wrong category: {prod['categoria']}"
        
        print(f"✅ GET /api/prodotti?categoria=Latticini: {len(data)} products")
    
    def test_get_prodotti_in_offerta(self):
        """Get products on sale"""
        response = requests.get(f"{BASE_URL}/api/prodotti", params={"in_offerta": True})
        assert response.status_code == 200
        
        data = response.json()
        # Some products should be on sale
        for prod in data:
            assert prod["in_offerta"] == True, f"Product not on sale: {prod['nome_prodotto']}"
        
        print(f"✅ GET /api/prodotti?in_offerta=true: {len(data)} products on sale")
    
    def test_get_prodotti_search(self):
        """Get products with search filter"""
        response = requests.get(f"{BASE_URL}/api/prodotti", params={"search": "latte"})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "No products found for 'latte'"
        
        # Verify search term is in product names
        for prod in data:
            assert "latte" in prod["nome_prodotto"].lower(), f"Search mismatch: {prod['nome_prodotto']}"
        
        print(f"✅ GET /api/prodotti?search=latte: {len(data)} products")
    
    def test_autocomplete_prodotti(self):
        """Test product autocomplete"""
        response = requests.get(f"{BASE_URL}/api/prodotti/autocomplete", params={"q": "latte"})
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            # Verify suggestions contain search term
            for suggestion in data:
                assert "latte" in suggestion.lower(), f"Autocomplete mismatch: {suggestion}"
        
        print(f"✅ GET /api/prodotti/autocomplete?q=latte: {len(data)} suggestions")
    
    def test_get_categorie(self):
        """Get all product categories"""
        response = requests.get(f"{BASE_URL}/api/categorie")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 12, f"Expected 12 categories, got {len(data)}"
        
        for expected_cat in EXPECTED_CATEGORIES:
            assert expected_cat in data, f"Missing category: {expected_cat}"
        
        print(f"✅ GET /api/categorie: {len(data)} categories")


class TestScraperEndpoints:
    """Test scraper endpoints - requires authentication"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for scraper tests"""
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"TEST_scraper_{unique_id}@test.com"
        
        # Register user
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "ScraperTest123!",
            "nome": f"Scraper Test {unique_id}"
        })
        
        if response.status_code == 200:
            return response.json()["access_token"]
        
        # If registration fails, try login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_prezzi@test.com",
            "password": "test123"
        })
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        
        pytest.skip("Could not get auth token")
    
    def test_scraper_categories(self, auth_token):
        """Test GET /api/scraper/categories - returns 12 categories with search terms"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/scraper/categories", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert len(data) == 12, f"Expected 12 categories, got {len(data)}"
        
        # Verify structure - each category has list of search terms
        for cat, terms in data.items():
            assert isinstance(terms, list), f"Terms for {cat} should be a list"
            assert len(terms) > 0, f"Category {cat} has no search terms"
        
        print(f"✅ GET /api/scraper/categories: {len(data)} categories")
        for cat, terms in data.items():
            print(f"   {cat}: {len(terms)} terms")
    
    def test_scraper_status(self, auth_token):
        """Test GET /api/scraper/status - returns scraping status"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/scraper/status", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "in_corso" in data
        assert "ultimo_scraping" in data
        assert "log" in data
        
        print(f"✅ GET /api/scraper/status: in_corso={data['in_corso']}")
    
    def test_scraper_log(self, auth_token):
        """Test GET /api/scraper/log - returns scraping history"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/scraper/log", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        
        print(f"✅ GET /api/scraper/log: {len(data)} log entries")
    
    def test_scraper_search_preview(self, auth_token):
        """Test POST /api/scraper/search-preview - returns real DoveConviene prices"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/scraper/search-preview",
            headers=headers,
            params={"search_term": "latte"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "search_term" in data
        assert data["search_term"] == "latte"
        assert "risultati" in data
        assert "prodotti" in data
        
        # Should return some results from DoveConviene
        print(f"✅ POST /api/scraper/search-preview?search_term=latte: {data['risultati']} results")
        
        if data["risultati"] > 0:
            # Verify product structure
            first_prod = data["prodotti"][0]
            assert "nome_prodotto" in first_prod
            assert "prezzo" in first_prod
            assert "negozio_originale" in first_prod
            print(f"   Sample: {first_prod['nome_prodotto']} - €{first_prod['prezzo']} at {first_prod['negozio_originale']}")
    
    def test_scraper_run_single_term(self, auth_token):
        """Test POST /api/scraper/run with search_term - triggers background scraping"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First check if scraping is already in progress
        status_response = requests.get(f"{BASE_URL}/api/scraper/status", headers=headers)
        if status_response.json().get("in_corso"):
            print("⚠️ Scraping already in progress, skipping run test")
            pytest.skip("Scraping already in progress")
        
        response = requests.post(
            f"{BASE_URL}/api/scraper/run",
            headers=headers,
            params={"search_term": "pasta"}
        )
        
        # Could be 200 (started) or 409 (already running)
        assert response.status_code in [200, 409], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert data["tipo"] == "singolo"
            print(f"✅ POST /api/scraper/run?search_term=pasta: {data['message']}")
            
            # Wait a bit and check status
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/scraper/status", headers=headers)
            status = status_response.json()
            print(f"   Status after 2s: in_corso={status['in_corso']}")
        else:
            print("⚠️ Scraping already in progress (409)")
    
    def test_scraper_requires_auth(self):
        """Test that scraper endpoints require authentication"""
        # No auth header
        response = requests.get(f"{BASE_URL}/api/scraper/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Scraper endpoints require authentication")


class TestOfferte:
    """Test offers endpoint"""
    
    def test_get_offerte(self):
        """Get products on sale grouped by supermarket"""
        response = requests.get(f"{BASE_URL}/api/prodotti/offerte")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict)
        
        total_offers = sum(len(offers) for offers in data.values())
        print(f"✅ GET /api/prodotti/offerte: {total_offers} offers across {len(data)} stores")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
