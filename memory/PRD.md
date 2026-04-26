# Shopply - PRD

## Problema Originale
App web per ottimizzare la spesa al supermercato tra piu catene, copertura tutta Italia.

## Funzionalita Implementate

### v4.2.0 - Mappa Interattiva + Scraping Potenziato (26 Aprile 2026)
- **Mappa Leaflet interattiva** nella pagina Offerte con marker colorati per catena (21 colori brand)
- **Marker posizione utente** (verde) al centro della mappa
- **Toggle Mappa/Lista** per switch rapido tra visualizzazione mappa e lista offerte
- **Popup informativi**: click su marker mostra nome negozio, indirizzo, distanza, offerte top, sconti migliori
- **Scroll-to-store**: click su marker chiude mappa e scrolla alla sezione del negozio
- **Indirizzo reale OSM** mostrato nell'header di ogni sezione supermercato
- **Scraping DoveConviene potenziato**: da 15 a 40+ search terms coprendo tutte le categorie (Latticini, Cereali, Frutta, Carne, Bevande, Snack, Condimenti, Surgelati, Igiene, Baby, Pet)
- **Endpoint manuale scraping**: POST /api/supermercati/scrape-offerte per trigger manuale
- **Log scraping**: ogni sessione di scraping viene registrata in scraping_log

### v4.1.0 - Supermercati e Offerte Reali (26 Aprile 2026)
- Discovery reale OpenStreetMap Overpass API (536+ negozi Pioltello, 112+ Catania)
- Catalogo prodotti base per negozi scoperti, scraping DoveConviene in background
- Deduplicazione OSM/seed, cache discovery 7 giorni, copertura nazionale

### v4.0.0 - Ranking Personalizzato Offerte (20 Aprile 2026)
- Motore raccomandazione scoring 0-100, cold-start fallback, blended mode
- UI labels personalizzate, sezione "Consigliati per te", debug mode

### v3.1.0 - Offerte Geolocalizzate
### v3.0.0 - Click-to-Add + Product Tooltip
### v2.8.0 - Backend Refactoring (13 moduli)
### v2.7.0 - Fuzzy Matching + Scraping Multi-Fonte
### Core: Auth JWT, liste spesa, ottimizzazione prezzi, mappa, PWA, referral, notifiche, famiglia

## Architettura
- Backend: FastAPI modulare (routes/, ranking_engine.py, store_discovery.py, catalog_generator.py, scraper.py)
- Frontend: React + TailwindCSS + Leaflet + Framer Motion
- Database: MongoDB (motor async)
- APIs: OpenStreetMap Overpass, DoveConviene, Open Food Facts, Nominatim

## Backlog
### P1: Missioni Giornaliere/Settimanali (gamification)
### P2: Scraping scheduling automatico (cron-style)
### P2: Espansione nazionale Q2 2026
### P3: Assistenti Vocali
