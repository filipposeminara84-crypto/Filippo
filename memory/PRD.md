# Shopply - PRD (Product Requirements Document)

## Problema Originale
App web per ottimizzare la spesa al supermercato, trovando i migliori prezzi tra piu supermercati.

## Stack Tecnologico
- **Frontend**: React.js, TailwindCSS, Framer Motion, Leaflet, lucide-react
- **Backend**: FastAPI, Python, MongoDB (motor), JWT auth
- **Architettura**: SPA con REST API, PWA

## Funzionalita Implementate

### MVP - V2.2
- Auth, liste spesa, ottimizzazione prezzi, mappa, PWA, referral, notifiche, condivisione familiare, password reset

### V2.3 - Scraping Prezzi
- Scraping reale da DoveConviene.it, pagina Gestione Prezzi, 12 categorie

### V2.4 - Geolocalizzazione
- Selettore posizione manuale, autocomplete migliorato, catalogo prodotti unici

### V2.5 - GPS + Reverse Geocoding
- "Usa posizione attuale" con reverse geocoding Nominatim (Via X, Citta)

### V2.6 (24 Marzo 2026) - Espansione Lombardia + Sicilia
- **33 Supermercati** in 6 citta: Pioltello(8), Segrate(3), Cernusco(1), Gallarate(9), Catania(7), Palermo(5)
- **6963 Prodotti** con prezzi regionali (Sicilia ~3% markup trasporto)
- **Nuove catene**: Il Gigante, Deco (160+ pdv Sicilia), Ipercoop
- **GET /api/supermercati/nearby**: Ricerca per coordinate + raggio km
- **GET /api/copertura**: Zone coperte con conteggio negozi per citta
- **LocationPicker aggiornato**: Sezioni Lombardia/Sicilia, 10 preset, messaggio copertura
- **Scraper aggiornato**: CHAIN_MAP con Il Gigante, Deco, Ipercoop

## Copertura Geografica
| Regione | Citta | Negozi | Catene |
|---------|-------|--------|--------|
| Lombardia | Pioltello | 8 | Coop, Esselunga, Lidl, Eurospin, Carrefour, Penny, Conad, Aldi |
| Lombardia | Segrate | 3 | MD, Carrefour, Aldi |
| Lombardia | Cernusco | 1 | Unes |
| Lombardia | Gallarate | 9 | Esselunga x2, Conad, Coop, Carrefour, Lidl, Iperal, Il Gigante, MD |
| Sicilia | Catania | 7 | Conad x2, Deco x2, Eurospin, Lidl, Ipercoop |
| Sicilia | Palermo | 5 | Conad, Deco, Eurospin, Lidl, Ipercoop |

## API Principali
- Auth: login, register, forgot-password, reset-password
- Supermercati: getAll, nearby(lat,lng,raggio), copertura, getById
- Prodotti: getAll(+filtri+paginazione), autocomplete, offerte, catalogo
- Scraper: run, status, log, categories, search-preview
- Liste: CRUD + condivisione
- Ottimizzazione: ottimizza

## Backlog
### P2
- Missioni Giornaliere/Settimanali
### P3
- Integrazione Assistenti Vocali
- Espansione nazionale (prevista Q2 2026)
