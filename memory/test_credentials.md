# Shopply Test Credentials

## Test Users (created via POST /api/acquisti/seed-mock)

| Role | Email | Password | Profile |
|------|-------|----------|---------|
| Heavy Buyer | heavy_buyer@test.com | test1234 | Latticini-focused, Esselunga/Coop preference |
| Discount Hunter | discount_hunter@test.com | test1234 | Lidl/Eurospin/MD, discount-oriented |
| New User (Cold Start) | new_user@test.com | test1234 | No purchase history |

## Notes
- All users created with JWT auth flow
- Login: POST /api/auth/login with { email, password }
- Mock purchases seeded via: POST /api/acquisti/seed-mock
- Real stores discovered via: POST /api/supermercati/discover?lat=X&lng=Y
