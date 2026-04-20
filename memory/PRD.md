# Shopply - PRD

## Problema Originale
App web per ottimizzare la spesa al supermercato tra piu catene, copertura Lombardia e Sicilia.

## Funzionalita Implementate

### v4.0.0 - Ranking Personalizzato Offerte (20 Aprile 2026)
- **Motore di raccomandazione**: scoring 0-100 con 7 fattori pesati (category 0.30, brand 0.20, product 0.15, recency 0.15, price_fit 0.10, distance 0.05, discount 0.05)
- **Bonus**: complementary products (+5), repeat purchase (+8), outlier price penalty (-5)
- **Cold-start fallback**: utenti con <3 ordini o <10 item → ranking per vicinanza + sconto + categorie essenziali
- **Blended mode**: 50% personalizzazione + 50% fallback per utenti con storico limitato
- **Diversity guardrails**: max 2 stessi categoria/supermercato consecutivi nei top 20
- **UI labels**: "Comprato spesso", "In base ai tuoi acquisti", "Vicino a te", "Ottimo sconto", "Da riordinare", "Prodotto correlato"
- **"Consigliati per te"** sezione dedicata con top 10 picks scrollabile
- **Debug mode**: ?debug=true mostra score breakdown per ogni offerta
- **Hook automatico**: mark_eseguita registra acquisti nello storico
- **Mock data seeder**: 3 profili test (heavy buyer, discount hunter, cold start)
- **Nuovi endpoint**: GET /api/offerte/personalizzate, POST /api/acquisti, GET /api/acquisti, POST /api/acquisti/bulk, POST /api/acquisti/seed-mock

### v3.1.0 - Offerte Geolocalizzate (28 Marzo 2026)
- Filtro geografico 15km, indicatore posizione, distanza negozio, warning senza posizione

### v3.0.0 - Click-to-Add + Product Tooltip
- Offerte cliccabili per aggiunta a lista, tooltip con foto Open Food Facts

### v2.8.0 - Backend Refactoring
- server.py suddiviso in 13 file modulari (/app/backend/routes/)

### v2.7.0 - Fuzzy Matching + Scraping Multi-Fonte
- Fuzzy Product Matching con normalizzazione quantita/suffissi

### Core Features
- Auth (JWT), liste spesa, ottimizzazione prezzi, mappa Leaflet, PWA
- Referral, notifiche, condivisione familiare, password reset
- Scraping DoveConviene.it, 12 categorie, 33 supermercati, ~7000 prodotti

## Architettura
- Backend: FastAPI modulare (routes/, models.py, ranking_engine.py, dependencies.py)
- Frontend: React + TailwindCSS + Leaflet + Framer Motion
- Database: MongoDB (motor async)
- Collections: utenti, prodotti, supermercati, liste_spesa, ricerche_storiche, storico_acquisti, notifiche, referrals, aggiornamenti_prezzi
- Immagini: Open Food Facts API + cache MongoDB

## Backlog
### P1: Missioni Giornaliere/Settimanali (gamification)
### P2: Integrazione Pepesto API
### P2: Espansione nazionale Q2 2026
### P3: Assistenti Vocali
