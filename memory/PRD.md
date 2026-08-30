# Shopply - PRD

## Problema Originale
App web per ottimizzare la spesa al supermercato tra piu catene, copertura tutta Italia.

## Funzionalita Implementate

### v4.3.0 - Google Sign-in (Emergent Auth) (30 Agosto 2026)
- **Google OAuth** via Emergent Auth: pulsante "Accedi con Google" sulla pagina login
- Flusso: login page → auth.emergentagent.com → callback con session_id → exchange per session
- Utenti Google auto-creati nella collection utenti con auth_provider: "google"
- Session cookie httpOnly + supporto dual-auth (JWT + session_token) in get_current_user
- AuthCallback component per gestire il redirect OAuth
- Logout Google: elimina session cookie e session dal DB
- JWT auth tradizionale preservato e funzionante

### v4.2.0 - Mappa Interattiva + Scraping Potenziato (26 Aprile 2026)
- Mappa Leaflet interattiva con marker colorati per catena (21+ colori brand)
- Toggle Mappa/Lista, popup informativi, scroll-to-store
- Scraping DoveConviene 40+ search terms, endpoint manuale scraping

### v4.1.0 - Supermercati e Offerte Reali (26 Aprile 2026)
- Discovery OpenStreetMap Overpass API (536+ negozi Pioltello, 112+ Catania)
- Catalogo base, scraping DoveConviene, deduplicazione OSM/seed, cache 7gg

### v4.0.0 - Ranking Personalizzato Offerte (20 Aprile 2026)
- Scoring 0-100, cold-start fallback, blended mode, diversity guardrails
- UI labels personalizzate, "Consigliati per te", debug mode

### v3.x - Offerte Geolocalizzate, Click-to-Add, Product Tooltip
### v2.x - Backend Refactoring, Fuzzy Matching
### Core: Auth JWT, liste spesa, ottimizzazione prezzi, mappa, PWA, referral, notifiche, famiglia

## Architettura
- Backend: FastAPI modulare (routes/, ranking_engine.py, store_discovery.py, catalog_generator.py, scraper.py)
- Frontend: React + TailwindCSS + Leaflet + Framer Motion
- Database: MongoDB (motor async)
- Auth: JWT (email/password) + Emergent Google OAuth (session cookies)
- APIs: OpenStreetMap Overpass, DoveConviene, Open Food Facts, Nominatim, Emergent Auth

## Backlog
### P1: Missioni Giornaliere/Settimanali (gamification)
### P2: Scraping scheduling automatico (cron-style)
### P2: Espansione nazionale Q2 2026
### P3: Assistenti Vocali
