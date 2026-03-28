# Shopply - PRD

## Problema Originale
App web per ottimizzare la spesa al supermercato tra piu catene, copertura Lombardia e Sicilia.

## Funzionalita Implementate (v2.8.0 - 28 Marzo 2026)

### Core
- Auth (JWT), liste spesa, ottimizzazione prezzi, mappa Leaflet, PWA, referral, notifiche, condivisione familiare, password reset
- Scraping reale DoveConviene.it, 12 categorie, pagina Gestione Prezzi multi-fonte
- 33 supermercati, ~7000 prodotti, 15 catene

### v2.8.0 - Backend Refactoring Completo
- **Architettura modulare**: server.py (1860 righe) suddiviso in 13 file:
  - `server.py` (59 righe) - entry point
  - `database.py` - connessione MongoDB
  - `models.py` - Pydantic models
  - `dependencies.py` - auth, helpers, product matching
  - `routes/auth.py` - autenticazione + password reset
  - `routes/ottimizza.py` - motore ottimizzazione + matrice prezzi
  - `routes/supermercati.py` - negozi + prodotti + categorie
  - `routes/liste.py` - liste spesa + condivisione
  - `routes/famiglia.py` - gruppi familiari
  - `routes/notifiche.py` - notifiche in-app
  - `routes/referral.py` - programma referral
  - `routes/scraper_routes.py` - scraping multi-fonte
  - `routes/seed.py` - seed database
- **Zero regressioni**: 37 test backend + tutti frontend passati al 100%

### v2.7.0 - Fuzzy Matching + Scraping Multi-Fonte
- Fuzzy Product Matching nell'algoritmo di ottimizzazione (suffissi quantita)
- Scraping Multi-Fonte: DoveConviene (primaria), Pepesto API (opzionale), Cross-Reference
- UI Gestione Prezzi con toggle fonti e badge colorati

### v2.6.2 - Geolocalizzazione
- LocationPicker con GPS fallback, reverse geocoding, persistenza localStorage

## Copertura
| Regione | Citta | Negozi |
|---------|-------|--------|
| Lombardia | Pioltello/Segrate/Cernusco | 12 |
| Lombardia | Gallarate | 9 |
| Sicilia | Catania | 7 |
| Sicilia | Palermo | 5 |

## Architettura Tecnica
- Backend: FastAPI modulare (routes/, models.py, dependencies.py)
- Frontend: React + TailwindCSS + Leaflet + Framer Motion
- Database: MongoDB (motor async driver)
- Scraping: httpx + BeautifulSoup4
- PWA: Service Worker + manifest.json
- Deploy: GitHub Pages (/app/docs/)

## Backlog
### P1: Missioni Giornaliere/Settimanali (gamification)
### P2: Integrazione Pepesto API (chiave API a pagamento)
### P2: Espansione nazionale Q2 2026
### P3: Assistenti Vocali
