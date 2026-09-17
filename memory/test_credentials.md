# Shopply Test Credentials

## Test Users (JWT Auth - created via POST /api/acquisti/seed-mock)

| Role | Email | Password | Profile |
|------|-------|----------|---------|
| Heavy Buyer | heavy_buyer@test.com | test1234 | Latticini-focused, Esselunga/Coop preference |
| Discount Hunter | discount_hunter@test.com | test1234 | Lidl/Eurospin/MD, discount-oriented |
| New User (Cold Start) | new_user@test.com | test1234 | No purchase history |

## Google Auth
- Google Sign-in via Emergent Auth: click "Accedi con Google" on /login page
- Redirects to auth.emergentagent.com → back to app with session
- Google users auto-created in utenti collection with auth_provider: "google"

## Notes
- Login: POST /api/auth/login with { email, password }
- Mock purchases seeded via: POST /api/acquisti/seed-mock
- Real stores discovered via: POST /api/supermercati/discover?lat=X&lng=Y
