"""
Test Suite for Shopply Auth Flows
- Tests login, register, forgot password endpoints
- Tests /reset-password route and token verification
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shopply-grocery.preview.emergentagent.com')

class TestHealthEndpoints:
    """Health check tests"""
    
    def test_api_root(self):
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        print("✅ API root endpoint working")
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health endpoint working")


class TestAuthRegisterLogin:
    """User registration and login flow tests"""
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """Generate unique test user credentials"""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "email": f"TEST_user_{unique_id}@test.com",
            "password": "TestPass123!",
            "nome": f"Test User {unique_id}"
        }
    
    def test_register_user(self, test_user):
        """Test user registration"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user["email"]
        assert data["user"]["nome"] == test_user["nome"]
        assert "referral_code" in data["user"]
        print(f"✅ User registration successful - referral_code: {data['user']['referral_code']}")
        
        # Store token for later tests
        test_user["token"] = data["access_token"]
        test_user["id"] = data["user"]["id"]
        return data
    
    def test_login_user(self, test_user):
        """Test user login with registered credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_user["email"]
        print("✅ Login successful")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@nonexistent.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print("✅ Invalid login correctly returns 401")
    
    def test_get_me_authenticated(self, test_user):
        """Test /auth/me endpoint with valid token"""
        if "token" not in test_user:
            # Register first
            self.test_register_user(test_user)
        
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == test_user["email"]
        print("✅ /auth/me endpoint working")
    
    def test_get_me_no_token(self):
        """Test /auth/me without token returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]
        print("✅ /auth/me correctly requires authentication")


class TestForgotPasswordFlow:
    """Tests for forgot password and reset password endpoints"""
    
    def test_forgot_password_existing_email(self):
        """Test forgot password for existing user"""
        # First create a test user
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"TEST_forgot_{unique_id}@test.com"
        
        # Register user
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "nome": f"Forgot Test {unique_id}"
        })
        assert register_response.status_code == 200
        
        # Request password reset
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": test_email
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        # In demo mode, token is returned for testing
        assert "demo_token" in data, "Demo token should be returned for testing"
        print(f"✅ Forgot password request successful, demo_token: {data['demo_token'][:20]}...")
        
        return {"email": test_email, "token": data["demo_token"]}
    
    def test_forgot_password_nonexistent_email(self):
        """Test forgot password for non-existent email (should not reveal if email exists)"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "nonexistent_user_xyz@notreal.com"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        # Should not reveal that email doesn't exist
        print("✅ Forgot password correctly handles non-existent email")
    
    def test_verify_reset_token_valid(self):
        """Test token verification with valid token"""
        # Get a valid token first
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"TEST_verify_{unique_id}@test.com"
        
        # Register and request reset
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "nome": f"Verify Test {unique_id}"
        })
        
        forgot_response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": test_email
        })
        token = forgot_response.json()["demo_token"]
        
        # Verify token
        response = requests.get(f"{BASE_URL}/api/auth/verify-reset-token", params={"token": token})
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] == True
        assert "email" in data  # Masked email like "tes***"
        print(f"✅ Token verification successful, masked email: {data['email']}")
    
    def test_verify_reset_token_invalid(self):
        """Test token verification with invalid token"""
        response = requests.get(f"{BASE_URL}/api/auth/verify-reset-token", params={"token": "invalid_token_xyz"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] == False
        assert "message" in data
        print("✅ Invalid token correctly returns valid=false")
    
    def test_reset_password_valid_token(self):
        """Test password reset with valid token"""
        # Get a valid token first
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"TEST_reset_{unique_id}@test.com"
        new_password = "NewTestPass456!"
        
        # Register
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "OldPassword123!",
            "nome": f"Reset Test {unique_id}"
        })
        
        # Request reset token
        forgot_response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": test_email
        })
        token = forgot_response.json()["demo_token"]
        
        # Reset password
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": token,
            "new_password": new_password
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        print("✅ Password reset successful")
        
        # Verify login with new password
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": new_password
        })
        assert login_response.status_code == 200
        print("✅ Login with new password successful")
    
    def test_reset_password_invalid_token(self):
        """Test password reset with invalid token returns 400"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": "invalid_token_abc",
            "new_password": "SomePassword123!"
        })
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        print("✅ Reset password with invalid token correctly returns 400")


class TestRegisterWithReferral:
    """Test registration with referral code"""
    
    def test_register_with_referral_code(self):
        """Test user registration with valid referral code"""
        # First create an inviting user
        unique_id1 = str(uuid.uuid4())[:8]
        inviter_email = f"TEST_inviter_{unique_id1}@test.com"
        
        inviter_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": inviter_email,
            "password": "InviterPass123!",
            "nome": f"Inviter {unique_id1}"
        })
        assert inviter_response.status_code == 200
        referral_code = inviter_response.json()["user"]["referral_code"]
        
        # Register new user with referral code
        unique_id2 = str(uuid.uuid4())[:8]
        invited_email = f"TEST_invited_{unique_id2}@test.com"
        
        invited_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": invited_email,
            "password": "InvitedPass123!",
            "nome": f"Invited {unique_id2}",
            "referral_code": referral_code
        })
        assert invited_response.status_code == 200
        
        data = invited_response.json()
        # Invited user should receive 25 bonus points
        assert data["user"]["punti_referral"] == 25
        print(f"✅ Registration with referral code successful, bonus points: {data['user']['punti_referral']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
