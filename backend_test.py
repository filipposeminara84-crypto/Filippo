#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class ShopplyReferralTester:
    def __init__(self, base_url="https://command-center-124.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", endpoint=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {name}: {details}")
        return success

    def run_test(self, name, method, endpoint, expected_status, data=None, require_auth=True):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if require_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if success:
                try:
                    response_data = response.json()
                    return self.log_test(name, True, f"{details} - Response OK", endpoint), response_data
                except:
                    return self.log_test(name, True, f"{details} - No JSON response", endpoint), {}
            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', str(error_data))
                except:
                    error_detail = response.text or "No error details"
                
                return self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}: {error_detail}", endpoint), {}

        except requests.exceptions.Timeout:
            return self.log_test(name, False, "Request timeout", endpoint), {}
        except Exception as e:
            return self.log_test(name, False, f"Error: {str(e)}", endpoint), {}

    def test_health_check(self):
        """Test basic connectivity"""
        success, _ = self.run_test("Health Check", "GET", "", 200, require_auth=False)
        return success

    def test_auth_system(self):
        """Test authentication with referral system"""
        print("\n🔐 Testing Authentication with Referral...")
        
        # Test user registration with referral
        test_timestamp = datetime.now().strftime('%H%M%S')
        mario_email = f"mario.test.{test_timestamp}@shopply.it"
        luigi_email = f"luigi.test.{test_timestamp}@shopply.it"
        
        # Register first user (Mario)
        mario_data = {
            "email": mario_email,
            "password": "test123",
            "nome": "Mario Rossi"
        }
        
        success, response = self.run_test(
            "Register Mario (Referrer)", "POST", "auth/register", 200, 
            mario_data, require_auth=False
        )
        
        if not success:
            return False
        
        mario_referral_code = response.get('user', {}).get('referral_code')
        mario_token = response.get('access_token')
        
        if not mario_referral_code:
            return self.log_test("Mario Referral Code Generation", False, "No referral code in response", "auth/register")
        
        self.log_test("Mario Referral Code Generation", True, f"Generated code: {mario_referral_code}", "auth/register")
        
        # Register second user with referral code (Luigi)
        luigi_data = {
            "email": luigi_email,
            "password": "test123",
            "nome": "Luigi Verdi",
            "referral_code": mario_referral_code
        }
        
        success, luigi_response = self.run_test(
            "Register Luigi (with Referral)", "POST", "auth/register", 200,
            luigi_data, require_auth=False
        )
        
        if not success:
            return False
        
        luigi_points = luigi_response.get('user', {}).get('punti_referral', 0)
        if luigi_points != 25:
            return self.log_test("Luigi Bonus Points", False, f"Expected 25 points, got {luigi_points}", "auth/register")
        
        self.log_test("Luigi Bonus Points", True, f"Received {luigi_points} points", "auth/register")
        
        # Test login
        login_data = {"email": mario_email, "password": "test123"}
        success, response = self.run_test(
            "Mario Login", "POST", "auth/login", 200,
            login_data, require_auth=False
        )
        
        if success:
            self.token = response.get('access_token')
            self.user_id = response.get('user', {}).get('id')
            
        return success

    def test_referral_stats(self):
        """Test referral statistics endpoint"""
        success, response = self.run_test(
            "Get Referral Stats", "GET", "referral/stats", 200
        )
        
        if success:
            required_fields = ['referral_code', 'punti_totali', 'inviti_completati', 'inviti_pendenti', 'bonus_disponibile']
            for field in required_fields:
                if field not in response:
                    return self.log_test(f"Referral Stats Field: {field}", False, f"Missing field {field}", "referral/stats")
            
            self.log_test("Referral Stats Complete", True, f"All fields present - Points: {response.get('punti_totali', 0)}", "referral/stats")
        
        return success

    def test_referral_invite(self):
        """Test sending referral invite"""
        test_email = f"invite.test.{datetime.now().strftime('%H%M%S')}@example.com"
        invite_data = {"email": test_email}
        
        success, response = self.run_test(
            "Send Referral Invite", "POST", "referral/invita", 200, invite_data
        )
        
        if success and 'message' in response:
            self.log_test("Referral Invite Response", True, f"Message: {response['message']}", "referral/invita")
        
        return success

    def test_referral_leaderboard(self):
        """Test referral leaderboard"""
        success, response = self.run_test(
            "Get Referral Leaderboard", "GET", "referral/classifica", 200
        )
        
        if success:
            if isinstance(response, list):
                self.log_test("Leaderboard Format", True, f"Returned {len(response)} entries", "referral/classifica")
            else:
                return self.log_test("Leaderboard Format", False, "Expected list format", "referral/classifica")
        
        return success

    def test_referral_redeem(self):
        """Test point redemption"""
        # First get current points
        success, stats = self.run_test(
            "Get Stats for Redeem", "GET", "referral/stats", 200
        )
        
        if not success:
            return False
        
        points = stats.get('punti_totali', 0)
        
        if points < 10:
            self.log_test("Point Redemption Skipped", True, f"Insufficient points ({points}) for redemption test", "referral/riscatta")
            return True
        
        # Test redemption with 10 points
        redeem_data = {"punti": 10}  # Note: API expects direct integer parameter
        
        # Create a proper POST request with punti as query parameter or body
        url = f"{self.base_url}/api/referral/riscatta"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            # Try as query parameter
            response = requests.post(f"{url}?punti=10", headers=headers, timeout=10)
            
            if response.status_code != 200:
                # Try as JSON body
                response = requests.post(url, json={"punti": 10}, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    # Try as form data
                    headers_form = headers.copy()
                    headers_form['Content-Type'] = 'application/x-www-form-urlencoded'
                    response = requests.post(url, data={"punti": 10}, headers=headers_form, timeout=10)
            
            success = response.status_code == 200
            if success:
                try:
                    resp_data = response.json()
                    self.log_test("Point Redemption", True, f"Redeemed 10 points - {resp_data.get('message', '')}", "referral/riscatta")
                except:
                    self.log_test("Point Redemption", True, f"Status: {response.status_code}", "referral/riscatta")
            else:
                error_msg = "Unknown error"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', str(error_data))
                except:
                    error_msg = response.text
                
                self.log_test("Point Redemption", False, f"Status: {response.status_code} - {error_msg}", "referral/riscatta")
            
            return success
            
        except Exception as e:
            return self.log_test("Point Redemption", False, f"Error: {str(e)}", "referral/riscatta")

    def test_referral_invites_list(self):
        """Test getting list of sent invites"""
        success, response = self.run_test(
            "Get Referral Invites List", "GET", "referral/inviti", 200
        )
        
        if success:
            if isinstance(response, list):
                self.log_test("Invites List Format", True, f"Returned {len(response)} invites", "referral/inviti")
            else:
                return self.log_test("Invites List Format", False, "Expected list format", "referral/inviti")
        
        return success

    def test_generate_referral_code(self):
        """Test generating referral code for existing user"""
        success, response = self.run_test(
            "Generate Referral Code", "POST", "referral/genera-codice", 200
        )
        
        if success and 'referral_code' in response:
            self.log_test("Code Generation Response", True, f"Code: {response['referral_code']}", "referral/genera-codice")
        
        return success

    def test_other_endpoints(self):
        """Test other essential endpoints"""
        endpoints = [
            ("Get User Profile", "GET", "auth/me", 200),
            ("Get Supermercati", "GET", "supermercati", 200),
            ("Get Categories", "GET", "categorie", 200),
            ("Health Check", "GET", "health", 200)
        ]
        
        all_passed = True
        for name, method, endpoint, expected_status in endpoints:
            success, _ = self.run_test(name, method, endpoint, expected_status, require_auth=(endpoint != "health"))
            if not success:
                all_passed = False
        
        return all_passed

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Shopply Referral System Test Suite")
        print(f"Backend URL: {self.base_url}")
        
        # Test basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed, stopping tests")
            return self.generate_report()
        
        # Test authentication with referral
        if not self.test_auth_system():
            print("❌ Authentication failed, stopping referral tests")
            return self.generate_report()
        
        # Test referral endpoints
        self.test_referral_stats()
        self.test_referral_invite()
        self.test_referral_leaderboard() 
        self.test_referral_redeem()
        self.test_referral_invites_list()
        self.test_generate_referral_code()
        
        # Test other endpoints
        self.test_other_endpoints()
        
        return self.generate_report()

    def generate_report(self):
        """Generate final test report"""
        print(f"\n📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        failed_tests = [test for test in self.test_results if not test['success']]
        
        report = {
            "summary": f"Referral system testing completed - {self.tests_passed}/{self.tests_run} tests passed",
            "success_rate": f"{success_rate:.1f}%",
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": len(failed_tests),
            "test_details": self.test_results,
            "failed_test_details": failed_tests
        }
        
        # Print failed tests summary
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['details']}")
        
        return success_rate >= 80  # Consider 80%+ as passing


def main():
    tester = ShopplyReferralTester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())