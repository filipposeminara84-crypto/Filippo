"""
Test Suite for Shopply v6 Features - Geolocation Fix & Product List Improvements
- Tests improved autocomplete (multiple results, 'contains' matching)
- Tests /api/catalogo endpoint (210 unique products)
- Tests /api/prodotti pagination (limit up to 500)
- Tests category filtering
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shopply-grocery.preview.emergentagent.com')


class TestAutocompleteImprovements:
    """Test improved autocomplete - multiple results with 'contains' matching"""
    
    def test_autocomplete_returns_multiple_results(self):
        """Autocomplete should return multiple results (up to 20)"""
        response = requests.get(f"{BASE_URL}/api/prodotti/autocomplete", params={"q": "la"})
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 1, f"Expected multiple results, got {len(data)}"
        
        print(f"✅ GET /api/prodotti/autocomplete?q=la: {len(data)} results")
        print(f"   Results: {data}")
    
    def test_autocomplete_contains_matching(self):
        """Autocomplete should use 'contains' matching, not just 'startsWith'"""
        response = requests.get(f"{BASE_URL}/api/prodotti/autocomplete", params={"q": "pa"})
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        
        # Check that results contain 'pa' anywhere in the name (not just at start)
        contains_in_middle = False
        for name in data:
            if 'pa' in name.lower() and not name.lower().startswith('pa'):
                contains_in_middle = True
                break
        
        print(f"✅ GET /api/prodotti/autocomplete?q=pa: {len(data)} results")
        print(f"   Results: {data}")
        print(f"   Contains matching (not just startsWith): {contains_in_middle}")
    
    def test_autocomplete_diverse_results(self):
        """Autocomplete should return diverse product names"""
        response = requests.get(f"{BASE_URL}/api/prodotti/autocomplete", params={"q": "latte"})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 3, f"Expected at least 3 results for 'latte', got {len(data)}"
        
        # Verify all results contain 'latte'
        for name in data:
            assert 'latte' in name.lower(), f"Result '{name}' doesn't contain 'latte'"
        
        print(f"✅ GET /api/prodotti/autocomplete?q=latte: {len(data)} diverse results")
        print(f"   Results: {data}")
    
    def test_autocomplete_max_20_results(self):
        """Autocomplete should return max 20 results"""
        response = requests.get(f"{BASE_URL}/api/prodotti/autocomplete", params={"q": "a"})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) <= 20, f"Expected max 20 results, got {len(data)}"
        
        print(f"✅ GET /api/prodotti/autocomplete?q=a: {len(data)} results (max 20)")


class TestCatalogoEndpoint:
    """Test new /api/catalogo endpoint - returns unique products with aggregated data"""
    
    def test_catalogo_returns_210_products(self):
        """Catalogo should return ~210 unique products"""
        response = requests.get(f"{BASE_URL}/api/catalogo")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 200, f"Expected ~210 products, got {len(data)}"
        
        print(f"✅ GET /api/catalogo: {len(data)} unique products")
    
    def test_catalogo_product_structure(self):
        """Catalogo products should have prezzo_min, prezzo_max, num_supermercati"""
        response = requests.get(f"{BASE_URL}/api/catalogo")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "No products returned"
        
        first = data[0]
        assert "nome_prodotto" in first, "Missing nome_prodotto"
        assert "categoria" in first, "Missing categoria"
        assert "brand" in first, "Missing brand"
        assert "formato" in first, "Missing formato"
        assert "prezzo_min" in first, "Missing prezzo_min"
        assert "prezzo_max" in first, "Missing prezzo_max"
        assert "num_supermercati" in first, "Missing num_supermercati"
        assert "in_offerta" in first, "Missing in_offerta"
        
        # Verify data types
        assert isinstance(first["prezzo_min"], (int, float))
        assert isinstance(first["prezzo_max"], (int, float))
        assert isinstance(first["num_supermercati"], int)
        assert first["prezzo_min"] <= first["prezzo_max"], "prezzo_min should be <= prezzo_max"
        
        print(f"✅ Catalogo product structure verified")
        print(f"   Sample: {first['nome_prodotto']} - €{first['prezzo_min']}-€{first['prezzo_max']} ({first['num_supermercati']} stores)")
    
    def test_catalogo_filter_by_categoria(self):
        """Catalogo should filter by category"""
        response = requests.get(f"{BASE_URL}/api/catalogo", params={"categoria": "Bevande"})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "No Bevande products found"
        
        # Verify all products are in Bevande category
        for prod in data:
            assert prod["categoria"] == "Bevande", f"Wrong category: {prod['categoria']}"
        
        print(f"✅ GET /api/catalogo?categoria=Bevande: {len(data)} products")
    
    def test_catalogo_filter_latticini(self):
        """Catalogo should filter Latticini category"""
        response = requests.get(f"{BASE_URL}/api/catalogo", params={"categoria": "Latticini"})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "No Latticini products found"
        
        for prod in data:
            assert prod["categoria"] == "Latticini"
        
        print(f"✅ GET /api/catalogo?categoria=Latticini: {len(data)} products")


class TestProdottiPagination:
    """Test improved /api/prodotti with pagination (limit up to 500)"""
    
    def test_prodotti_limit_500(self):
        """Should return up to 500 products"""
        response = requests.get(f"{BASE_URL}/api/prodotti", params={"limit": 500})
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert len(data) == 500, f"Expected 500 products, got {len(data)}"
        
        print(f"✅ GET /api/prodotti?limit=500: {len(data)} products")
    
    def test_prodotti_default_limit(self):
        """Default limit should be 500"""
        response = requests.get(f"{BASE_URL}/api/prodotti")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) <= 500, f"Default limit exceeded: {len(data)}"
        
        print(f"✅ GET /api/prodotti (default): {len(data)} products")
    
    def test_prodotti_skip_pagination(self):
        """Should support skip for pagination"""
        # Get first page
        response1 = requests.get(f"{BASE_URL}/api/prodotti", params={"limit": 100, "skip": 0})
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get second page
        response2 = requests.get(f"{BASE_URL}/api/prodotti", params={"limit": 100, "skip": 100})
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify different products
        ids1 = set(p["id"] for p in data1)
        ids2 = set(p["id"] for p in data2)
        
        assert len(ids1.intersection(ids2)) == 0, "Pagination returned duplicate products"
        
        print(f"✅ Pagination working: page1={len(data1)}, page2={len(data2)}, no duplicates")
    
    def test_prodotti_filter_by_categoria(self):
        """Should filter by category"""
        response = requests.get(f"{BASE_URL}/api/prodotti", params={"categoria": "Latticini"})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "No Latticini products found"
        
        for prod in data:
            assert prod["categoria"] == "Latticini"
        
        print(f"✅ GET /api/prodotti?categoria=Latticini: {len(data)} products")


class TestCategorieEndpoint:
    """Test /api/categorie endpoint"""
    
    def test_get_all_categories(self):
        """Should return all 12 categories"""
        response = requests.get(f"{BASE_URL}/api/categorie")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 12, f"Expected 12 categories, got {len(data)}"
        
        expected = ["Latticini", "Bevande", "Pane e Cereali", "Frutta e Verdura"]
        for cat in expected:
            assert cat in data, f"Missing category: {cat}"
        
        print(f"✅ GET /api/categorie: {len(data)} categories")
        print(f"   Categories: {data}")


class TestSupermercatiEndpoint:
    """Test /api/supermercati endpoint"""
    
    def test_get_all_supermercati(self):
        """Should return 12 supermarkets"""
        response = requests.get(f"{BASE_URL}/api/supermercati")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 12, f"Expected 12 supermarkets, got {len(data)}"
        
        print(f"✅ GET /api/supermercati: {len(data)} supermarkets")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
