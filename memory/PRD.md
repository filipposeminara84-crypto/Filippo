# Shopply - PRD

## Problema Originale
App web per ottimizzare la spesa al supermercato tra piu catene, copertura tutta Italia.

## Funzionalita Implementate

### v4.1.0 - Supermercati e Offerte Reali (26 Aprile 2026)
- **Discovery reale**: integrazione OpenStreetMap Overpass API per scoprire TUTTI i supermercati reali vicini all'utente
- **536+ negozi a Pioltello, 112+ a Catania**: Il Gigante, Esselunga, Lidl, Conad, Coop, Aldi, Carrefour, Eurospin, Penny, Sigma, MD, Unes, Despar, Pam, Bennet, Famila, DPiu, iN's, Tocal, Deco, NaturaSi, etc.
- **Catalogo prodotti base**: generazione automatica catalogo per negozi scoperti con prezzi realistici per catena
- **Scraping DoveConviene**: offerte reali importate in background per catene scoperte
- **Deduplicazione**: quando ci sono negozi OSM reali, i dati seed vengono esclusi automaticamente
- **Cache discovery**: risultati OSM cached 7 giorni per evitare chiamate ripetute
- **Copertura nazionale**: funziona in qualsiasi citta' italiana (Overpass copre tutta Italia)
- **Nuovi moduli**: store_discovery.py, catalog_generator.py
- **Nuovo endpoint**: POST /api/supermercati/discover

### v4.0.0 - Ranking Personalizzato Offerte (20 Aprile 2026)
- Motore di raccomandazione scoring 0-100 (7 fattori + bonus)
- Cold-start fallback, blended mode, diversity guardrails
- UI labels: "Comprato spesso", "Da riordinare", "Vicino a te", "Ottimo sconto", "Prodotto correlato"
- Sezione "Consigliati per te", debug mode, hook automatico acquisti

### v3.1.0 - Offerte Geolocalizzate
- Filtro geografico 15km, indicatore posizione, distanza negozio

### v3.0.0 - Click-to-Add + Product Tooltip
- Offerte cliccabili, tooltip con foto Open Food Facts

### v2.8.0 - Backend Refactoring
- server.py suddiviso in 13+ file modulari

### v2.7.0 - Fuzzy Matching + Scraping Multi-Fonte
- Fuzzy Product Matching con normalizzazione

### Core Features
- Auth (JWT), liste spesa, ottimizzazione prezzi, mappa Leaflet, PWA
- Referral, notifiche, condivisione familiare, password reset

## Architettura
- Backend: FastAPI modulare (routes/, models.py, ranking_engine.py, store_discovery.py, catalog_generator.py, scraper.py)
- Frontend: React + TailwindCSS + Leaflet + Framer Motion
- Database: MongoDB (motor async)
- Collections: utenti, prodotti, supermercati, liste_spesa, ricerche_storiche, storico_acquisti, notifiche, referrals, aggiornamenti_prezzi, discovery_cache
- APIs Esterne: OpenStreetMap Overpass (stores), DoveConviene (offerte), Open Food Facts (immagini), Nominatim (geocoding)

## Backlog
### P1: Missioni Giornaliere/Settimanali (gamification)
### P2: Espansione scraping offerte reali (piu fonti)
### P2: Espansione nazionale Q2 2026
### P3: Assistenti Vocali
