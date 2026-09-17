# Auth Testing Playbook for Shopply

## Test Identity Tracking
After setting up Google Auth, test with Google accounts.

## Step 1: Create Test Session
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
# Test session via existing JWT
TOKEN=$(curl -s -X POST "$API_URL/api/auth/login" -H "Content-Type: application/json" -d '{"email":"heavy_buyer@test.com","password":"test1234"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s "$API_URL/api/auth/me" -H "Authorization: Bearer $TOKEN"
```

## Step 2: Test Google Auth Flow
1. Navigate to /login
2. Click "Accedi con Google"
3. Complete Google sign-in
4. Verify redirect back to app with session_id in URL hash
5. Verify user lands on dashboard

## Step 3: Verify Session Cookie Auth
```bash
curl -s "$API_URL/api/auth/me" -H "Cookie: session_token=YOUR_TOKEN"
```

## Checklist
- [ ] Google sign-in button visible on login page
- [ ] Clicking redirects to auth.emergentagent.com
- [ ] After Google auth, redirects back with session_id
- [ ] AuthCallback exchanges session_id for session
- [ ] User lands on dashboard
- [ ] /api/auth/me works with session_token cookie
- [ ] Existing JWT auth still works
- [ ] Logout clears session
