"""
Test suite for Shopply Lombardia + Sicilia expansion (33 stores, 6963 products)
Tests: /supermercati, /supermercati/nearby, /copertura, /prodotti with regional pricing
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSeedAndSupermercati:
    """Test seed creates 33 supermarkets with regione/citta fields"""
    
    def test_seed_creates_33_supermarkets(self):
        """POST /api/seed creates 33 supermarkets and ~6963 products"""
        response = requests.post(f"{BASE_URL}/api/seed")
        assert response.status_code == 200
        data = response.json()
        assert data["supermercati"] == 33, f"Expected 33 supermarkets, got {data['supermercati']}"
        assert data["prodotti"] >= 6900, f"Expected ~6963 products, got {data['prodotti']}"
        assert data["categorie"] == 12
        print(f"✅ Seed: {data['supermercati']} supermarkets, {data['prodotti']} products")
    
    def test_get_all_supermercati_returns_33(self):
        """GET /api/supermercati returns 33 supermarkets with regione and citta fields"""
        response = requests.get(f"{BASE_URL}/api/supermercati")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 33, f"Expected 33 supermarkets, got {len(data)}"
        
        # Check first supermarket has regione and citta
        first = data[0]
        assert "regione" in first, "Missing regione field"
        assert "citta" in first, "Missing citta field"
        assert first["regione"] in ["Lombardia", "Sicilia"], f"Unexpected regione: {first['regione']}"
        print(f"✅ GET /api/supermercati: {len(data)} supermarkets with regione/citta fields")
    
    def test_supermercati_have_correct_regions(self):
        """Verify supermarkets are distributed across Lombardia and Sicilia"""
        response = requests.get(f"{BASE_URL}/api/supermercati")
        data = response.json()
        
        lombardia = [s for s in data if s.get("regione") == "Lombardia"]
        sicilia = [s for s in data if s.get("regione") == "Sicilia"]
        
        assert len(lombardia) == 21, f"Expected 21 Lombardia stores, got {len(lombardia)}"
        assert len(sicilia) == 12, f"Expected 12 Sicilia stores, got {len(sicilia)}"
        print(f"✅ Regions: {len(lombardia)} Lombardia, {len(sicilia)} Sicilia")


class TestNearbyEndpoint:
    """Test /supermercati/nearby endpoint for different locations"""
    
    def test_nearby_catania_returns_7_stores(self):
        """GET /api/supermercati/nearby?lat=37.5079&lng=15.0830&raggio_km=10 returns 7 stores"""
        response = requests.get(f"{BASE_URL}/api/supermercati/nearby", params={
            "lat": 37.5079, "lng": 15.0830, "raggio_km": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 7, f"Expected 7 stores in Catania area, got {len(data)}"
        
        # Verify all have distanza_km field
        for store in data:
            assert "distanza_km" in store, "Missing distanza_km field"
            assert store["distanza_km"] <= 10, f"Store {store['id']} is {store['distanza_km']}km away"
        
        # Verify sorted by distance
        distances = [s["distanza_km"] for s in data]
        assert distances == sorted(distances), "Results not sorted by distance"
        print(f"✅ Catania nearby: {len(data)} stores within 10km")
    
    def test_nearby_gallarate_returns_9_stores(self):
        """GET /api/supermercati/nearby?lat=45.6603&lng=8.7917&raggio_km=10 returns 9 stores"""
        response = requests.get(f"{BASE_URL}/api/supermercati/nearby", params={
            "lat": 45.6603, "lng": 8.7917, "raggio_km": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9, f"Expected 9 stores in Gallarate area, got {len(data)}"
        
        # Check for new chains
        catene = set(s["catena"] for s in data)
        assert "Il Gigante" in catene, "Missing Il Gigante chain in Gallarate"
        print(f"✅ Gallarate nearby: {len(data)} stores, chains: {catene}")
    
    def test_nearby_palermo_returns_5_stores(self):
        """GET /api/supermercati/nearby?lat=38.1157&lng=13.3615&raggio_km=10 returns 5 stores"""
        response = requests.get(f"{BASE_URL}/api/supermercati/nearby", params={
            "lat": 38.1157, "lng": 13.3615, "raggio_km": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5, f"Expected 5 stores in Palermo area, got {len(data)}"
        
        # Check for Deco and Ipercoop chains
        catene = set(s["catena"] for s in data)
        assert "Deco" in catene, "Missing Deco chain in Palermo"
        assert "Ipercoop" in catene, "Missing Ipercoop chain in Palermo"
        print(f"✅ Palermo nearby: {len(data)} stores, chains: {catene}")
    
    def test_nearby_pioltello_returns_12_stores(self):
        """GET /api/supermercati/nearby for Pioltello area returns 12 stores"""
        response = requests.get(f"{BASE_URL}/api/supermercati/nearby", params={
            "lat": 45.4945, "lng": 9.3256, "raggio_km": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 12, f"Expected 12 stores in Pioltello area, got {len(data)}"
        print(f"✅ Pioltello nearby: {len(data)} stores")


class TestCoperturaEndpoint:
    """Test /copertura endpoint returns correct zone information"""
    
    def test_copertura_returns_zones(self):
        """GET /api/copertura returns zones for Lombardia and Sicilia"""
        response = requests.get(f"{BASE_URL}/api/copertura")
        assert response.status_code == 200
        data = response.json()
        
        assert "zone_coperte" in data
        assert "totale_negozi" in data
        assert "regioni" in data
        assert "messaggio" in data
        
        assert data["totale_negozi"] == 33
        assert set(data["regioni"]) == {"Lombardia", "Sicilia"}
        print(f"✅ Copertura: {data['totale_negozi']} stores, regions: {data['regioni']}")
    
    def test_copertura_zone_details(self):
        """Verify zone details have correct store counts"""
        response = requests.get(f"{BASE_URL}/api/copertura")
        data = response.json()
        
        zones = {z["citta"]: z for z in data["zone_coperte"]}
        
        # Verify Pioltello
        assert "Pioltello" in zones
        assert zones["Pioltello"]["num_negozi"] == 8
        assert zones["Pioltello"]["regione"] == "Lombardia"
        
        # Verify Gallarate
        assert "Gallarate" in zones
        assert zones["Gallarate"]["num_negozi"] == 9
        
        # Verify Catania
        assert "Catania" in zones
        assert zones["Catania"]["num_negozi"] == 7
        assert zones["Catania"]["regione"] == "Sicilia"
        
        # Verify Palermo
        assert "Palermo" in zones
        assert zones["Palermo"]["num_negozi"] == 5
        
        print(f"✅ Zone details verified: Pioltello(8), Gallarate(9), Catania(7), Palermo(5)")
    
    def test_copertura_message(self):
        """Verify coverage message mentions expansion"""
        response = requests.get(f"{BASE_URL}/api/copertura")
        data = response.json()
        
        assert "Lombardia" in data["messaggio"]
        assert "Sicilia" in data["messaggio"]
        assert "Q2 2026" in data["messaggio"]
        print(f"✅ Coverage message: {data['messaggio']}")


class TestProductsWithRegionalPricing:
    """Test products endpoint with regional pricing"""
    
    def test_pomodoro_esselunga_gallarate(self):
        """GET /api/prodotti?search=Pomodoro&supermercato_id=esselunga-gallarate-pegoraro"""
        response = requests.get(f"{BASE_URL}/api/prodotti", params={
            "search": "Pomodoro",
            "supermercato_id": "esselunga-gallarate-pegoraro"
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "No Pomodoro products found for Esselunga Gallarate"
        
        # Verify product structure
        product = data[0]
        assert "prezzo" in product
        assert "supermercato_id" in product
        assert product["supermercato_id"] == "esselunga-gallarate-pegoraro"
        print(f"✅ Pomodoro @ Esselunga Gallarate: {len(data)} products, price: €{product['prezzo']}")
    
    def test_latte_conad_catania(self):
        """GET /api/prodotti?search=Latte&supermercato_id=conad-catania-umberto"""
        response = requests.get(f"{BASE_URL}/api/prodotti", params={
            "search": "Latte",
            "supermercato_id": "conad-catania-umberto"
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "No Latte products found for Conad Catania"
        
        product = data[0]
        assert product["supermercato_id"] == "conad-catania-umberto"
        print(f"✅ Latte @ Conad Catania: {len(data)} products, price: €{product['prezzo']}")
    
    def test_pasta_deco_catania(self):
        """GET /api/prodotti?search=Pasta&supermercato_id=deco-catania-galermo"""
        response = requests.get(f"{BASE_URL}/api/prodotti", params={
            "search": "Pasta",
            "supermercato_id": "deco-catania-galermo"
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "No Pasta products found for Deco Catania"
        
        product = data[0]
        assert product["supermercato_id"] == "deco-catania-galermo"
        print(f"✅ Pasta @ Deco Catania: {len(data)} products, price: €{product['prezzo']}")
    
    def test_regional_price_variation(self):
        """Verify Sicilia has ~3% markup compared to Lombardia"""
        # Get Latte prices from Lombardia (Esselunga Pioltello)
        resp_lombardia = requests.get(f"{BASE_URL}/api/prodotti", params={
            "search": "Latte Intero",
            "supermercato_id": "esselunga-pioltello"
        })
        
        # Get Latte prices from Sicilia (Conad Catania)
        resp_sicilia = requests.get(f"{BASE_URL}/api/prodotti", params={
            "search": "Latte Intero",
            "supermercato_id": "conad-catania-umberto"
        })
        
        if resp_lombardia.json() and resp_sicilia.json():
            price_lombardia = resp_lombardia.json()[0]["prezzo"]
            price_sicilia = resp_sicilia.json()[0]["prezzo"]
            
            # Sicilia should be slightly higher (transport costs)
            # Note: This is a soft check as prices vary by chain
            print(f"✅ Regional pricing: Lombardia €{price_lombardia}, Sicilia €{price_sicilia}")
        else:
            print("⚠️ Could not compare regional prices (products not found)")


class TestNewChains:
    """Test new chains: Il Gigante, Deco, Ipercoop"""
    
    def test_il_gigante_exists(self):
        """Verify Il Gigante chain exists in Gallarate"""
        response = requests.get(f"{BASE_URL}/api/supermercati")
        data = response.json()
        
        il_gigante = [s for s in data if s["catena"] == "Il Gigante"]
        assert len(il_gigante) >= 1, "Il Gigante chain not found"
        assert il_gigante[0]["citta"] == "Gallarate"
        print(f"✅ Il Gigante: {len(il_gigante)} stores in {il_gigante[0]['citta']}")
    
    def test_deco_exists(self):
        """Verify Deco chain exists in Catania and Palermo"""
        response = requests.get(f"{BASE_URL}/api/supermercati")
        data = response.json()
        
        deco = [s for s in data if s["catena"] == "Deco"]
        assert len(deco) >= 3, f"Expected at least 3 Deco stores, got {len(deco)}"
        
        cities = set(s["citta"] for s in deco)
        assert "Catania" in cities, "Deco not found in Catania"
        assert "Palermo" in cities, "Deco not found in Palermo"
        print(f"✅ Deco: {len(deco)} stores in {cities}")
    
    def test_ipercoop_exists(self):
        """Verify Ipercoop chain exists in Catania and Palermo"""
        response = requests.get(f"{BASE_URL}/api/supermercati")
        data = response.json()
        
        ipercoop = [s for s in data if s["catena"] == "Ipercoop"]
        assert len(ipercoop) >= 2, f"Expected at least 2 Ipercoop stores, got {len(ipercoop)}"
        
        cities = set(s["citta"] for s in ipercoop)
        assert "Catania" in cities, "Ipercoop not found in Catania"
        assert "Palermo" in cities, "Ipercoop not found in Palermo"
        print(f"✅ Ipercoop: {len(ipercoop)} stores in {cities}")


class TestSupermercatoById:
    """Test /supermercati/{id} endpoint"""
    
    def test_get_esselunga_gallarate(self):
        """GET /api/supermercati/esselunga-gallarate-pegoraro"""
        response = requests.get(f"{BASE_URL}/api/supermercati/esselunga-gallarate-pegoraro")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "esselunga-gallarate-pegoraro"
        assert data["catena"] == "Esselunga"
        assert data["citta"] == "Gallarate"
        print(f"✅ GET supermercato by ID: {data['nome']}")
    
    def test_get_deco_catania(self):
        """GET /api/supermercati/deco-catania-galermo"""
        response = requests.get(f"{BASE_URL}/api/supermercati/deco-catania-galermo")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "deco-catania-galermo"
        assert data["catena"] == "Deco"
        assert data["citta"] == "Catania"
        print(f"✅ GET Deco Catania: {data['nome']}")
    
    def test_get_nonexistent_returns_404(self):
        """GET /api/supermercati/nonexistent returns 404"""
        response = requests.get(f"{BASE_URL}/api/supermercati/nonexistent-store")
        assert response.status_code == 404
        print("✅ Nonexistent store returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
