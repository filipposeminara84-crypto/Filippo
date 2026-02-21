import requests
import sys
import json
from datetime import datetime

class ShopplyAPITester:
    def __init__(self, base_url="https://command-center-124.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.text else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.failed_tests.append({
                    "test": name,
                    "endpoint": endpoint,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                try:
                    return False, response.json() if response.text else {}
                except:
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "endpoint": endpoint,
                "error": str(e)
            })
            return False, {}

    def test_health(self):
        """Test health endpoint"""
        return self.run_test("API Health Check", "GET", "api/health", 200)

    def test_seed_database(self):
        """Initialize database with seed data"""
        print(f"\n📊 Seeding database...")
        success, response = self.run_test("Seed Database", "POST", "api/seed", 200)
        if success:
            print(f"   Seeded: {response.get('supermercati', 0)} supermercati, {response.get('prodotti', 0)} prodotti")
        return success

    def test_register(self, email, password, nome):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "api/auth/register",
            200,
            data={"email": email, "password": password, "nome": nome}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Registered user: {response.get('user', {}).get('nome', 'Unknown')}")
            return True, response['user']
        return False, {}

    def test_login(self, email, password):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "api/auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Logged in user: {response.get('user', {}).get('nome', 'Unknown')}")
            return True, response['user']
        return False, {}

    def test_get_me(self):
        """Test get current user"""
        return self.run_test("Get Current User", "GET", "api/auth/me", 200)

    def test_get_supermercati(self):
        """Test get supermercati"""
        success, response = self.run_test("Get Supermercati", "GET", "api/supermercati", 200)
        if success:
            print(f"   Found {len(response)} supermercati")
        return success, response

    def test_autocomplete(self, query="latte"):
        """Test product autocomplete"""
        success, response = self.run_test(
            "Product Autocomplete",
            "GET",
            f"api/prodotti/autocomplete?q={query}",
            200
        )
        if success:
            print(f"   Found {len(response)} suggestions for '{query}'")
        return success, response

    def test_get_prodotti(self):
        """Test get products"""
        success, response = self.run_test("Get Prodotti", "GET", "api/prodotti", 200)
        if success:
            print(f"   Found {len(response)} prodotti")
        return success, response

    def test_create_lista(self, nome, prodotti):
        """Test create shopping list"""
        success, response = self.run_test(
            "Create Lista Spesa",
            "POST",
            "api/liste",
            200,
            data={"nome": nome, "prodotti": prodotti}
        )
        return success, response

    def test_get_liste(self):
        """Test get shopping lists"""
        return self.run_test("Get Liste Spesa", "GET", "api/liste", 200)

    def test_optimize_shopping(self, prodotti_lista):
        """Test shopping optimization"""
        success, response = self.run_test(
            "Optimize Shopping",
            "POST",
            "api/ottimizza",
            200,
            data={
                "lista_prodotti": prodotti_lista,
                "lat_utente": 45.4945,
                "lng_utente": 9.3256,
                "raggio_km": 5,
                "max_supermercati": 3,
                "peso_prezzo": 0.7,
                "peso_tempo": 0.3
            }
        )
        if success:
            piano = response.get('piano_ottimale', [])
            print(f"   Optimized plan: {len(piano)} stores, cost: €{response.get('costo_totale', 0)}")
            print(f"   Savings: €{response.get('risparmio_euro', 0)} ({response.get('risparmio_percentuale', 0)}%)")
        return success, response

    def test_get_storico(self):
        """Test get history"""
        return self.run_test("Get Storico", "GET", "api/storico", 200)

    def test_get_preferenze(self):
        """Test get preferences"""
        return self.run_test("Get Preferenze", "GET", "api/preferenze", 200)

    def test_update_preferenze(self):
        """Test update preferences"""
        prefs = {
            "raggio_max_km": 8,
            "max_supermercati": 4,
            "peso_prezzo": 0.6,
            "peso_tempo": 0.4,
            "supermercati_preferiti": ["coop-pioltello"]
        }
        return self.run_test("Update Preferenze", "PUT", "api/preferenze", 200, data=prefs)

    # ============== NEW V2.0 FEATURE TESTS ==============

    def test_get_offerte(self):
        """Test get offers endpoint"""
        success, response = self.run_test("Get Offerte", "GET", "api/prodotti/offerte", 200)
        if success:
            total_offers = sum(len(prods) for prods in response.values())
            print(f"   Found {total_offers} offers across {len(response)} stores")
        return success, response

    def test_get_categorie(self):
        """Test get categories endpoint"""
        success, response = self.run_test("Get Categorie", "GET", "api/categorie", 200)
        if success:
            print(f"   Found {len(response)} categories")
        return success, response

    def test_aggiorna_prezzi(self):
        """Test manual price update trigger"""
        success, response = self.run_test("Trigger Price Update", "POST", "api/prezzi/aggiorna", 200)
        if success:
            print(f"   Price update triggered: {response.get('message', '')}")
        return success, response

    def test_ultimo_aggiornamento(self):
        """Test get last price update info"""
        success, response = self.run_test("Get Last Update", "GET", "api/prezzi/ultimo-aggiornamento", 200)
        if success:
            if 'timestamp' in response:
                print(f"   Last update: {response.get('timestamp', '')}")
                print(f"   Products updated: {response.get('prodotti_aggiornati', 0)}")
            else:
                print(f"   {response.get('message', 'No updates')}")
        return success, response

    def test_get_notifiche(self):
        """Test get user notifications"""
        success, response = self.run_test("Get Notifiche", "GET", "api/notifiche", 200)
        if success:
            print(f"   Found {len(response)} notifications")
        return success, response

    def test_get_notifiche_non_lette(self):
        """Test get unread notifications count"""
        success, response = self.run_test("Get Unread Count", "GET", "api/notifiche/non-lette", 200)
        if success:
            print(f"   Unread notifications: {response.get('count', 0)}")
        return success, response

    def test_condividi_lista(self, lista_id, email_destinatario="famiglia@test.it"):
        """Test share shopping list functionality"""
        success, response = self.run_test(
            "Share Lista",
            "POST",
            f"api/liste/{lista_id}/condividi",
            200,
            data={"lista_id": lista_id, "email_destinatario": email_destinatario}
        )
        if success:
            print(f"   Shared list with: {email_destinatario}")
        return success, response

    def test_matrice_prezzi(self, prodotti=None):
        """Test price matrix endpoint"""
        if not prodotti:
            prodotti = ["Latte Intero 1L", "Pane in Cassetta"]
        success, response = self.run_test(
            "Get Price Matrix",
            "POST",
            "api/matrice-prezzi",
            200,
            data=prodotti
        )
        if success:
            print(f"   Price matrix for {len(prodotti)} products")
        return success, response

def main():
    print("🧪 Shopply API Testing Started")
    print("=" * 50)
    
    tester = ShopplyAPITester()
    
    # Test unique email for this run
    timestamp = datetime.now().strftime('%H%M%S')
    test_email = f"test_{timestamp}@shopply.it"
    test_password = "test123"
    test_nome = f"Tester {timestamp}"

    try:
        # 1. Basic health check
        print("\n📋 PHASE 1: Basic Connectivity")
        if not tester.test_health()[0]:
            print("❌ API health check failed - stopping all tests")
            return 1

        # 2. Seed database
        print("\n📋 PHASE 2: Database Initialization")
        if not tester.test_seed_database():
            print("⚠️ Seed failed but continuing with tests...")

        # 3. Authentication flow
        print("\n📋 PHASE 3: Authentication")
        
        # Register new user
        reg_success, user = tester.test_register(test_email, test_password, test_nome)
        if not reg_success:
            print("❌ Registration failed - stopping auth tests")
            return 1
            
        # Test get me
        if not tester.test_get_me()[0]:
            print("❌ Get current user failed")

        # Test login with existing user (from request)
        existing_success, existing_user = tester.test_login("test@shopply.it", "test123")
        if existing_success:
            print("✅ Login with existing test user successful")
        else:
            print("⚠️ Existing test user login failed - using registered user")

        # 4. Data retrieval
        print("\n📋 PHASE 4: Data Retrieval")
        
        # Get supermercati
        sup_success, supermercati = tester.test_get_supermercati()
        if not sup_success:
            print("❌ Failed to get supermercati")
            return 1

        # Autocomplete
        auto_success, suggestions = tester.test_autocomplete("latte")
        if not auto_success:
            print("⚠️ Autocomplete not working")

        # Get products
        prod_success, prodotti = tester.test_get_prodotti()
        if not prod_success:
            print("⚠️ Get prodotti failed")

        # 5. Shopping list operations
        print("\n📋 PHASE 5: Shopping Lists")
        
        # Create list
        test_prodotti = ["Latte Intero 1L", "Pane in Cassetta", "Mele Golden"]
        lista_success, lista = tester.test_create_lista("Lista Test", test_prodotti)
        if not lista_success:
            print("❌ Create lista failed")
        
        # Get lists
        if not tester.test_get_liste()[0]:
            print("⚠️ Get liste failed")

        # 6. Core optimization
        print("\n📋 PHASE 6: Shopping Optimization")
        opt_success, optimization = tester.test_optimize_shopping(test_prodotti)
        if not opt_success:
            print("❌ CRITICAL: Shopping optimization failed!")
            return 1

        # 7. History and preferences
        print("\n📋 PHASE 7: User Data")
        
        if not tester.test_get_storico()[0]:
            print("⚠️ Get storico failed")
        
        if not tester.test_get_preferenze()[0]:
            print("⚠️ Get preferenze failed")
        
        if not tester.test_update_preferenze()[0]:
            print("⚠️ Update preferenze failed")

        # Summary
        print("\n" + "=" * 50)
        print(f"📊 FINAL RESULTS")
        print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
        
        if tester.failed_tests:
            print(f"\n❌ Failed tests:")
            for fail in tester.failed_tests:
                print(f"   • {fail['test']}")
        
        success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        
        # Return success if >=80% pass rate and core optimization works
        if success_rate >= 80 and opt_success:
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())