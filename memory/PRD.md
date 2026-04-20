# Shopply - PRD

## Problema Originale
App web per ottimizzare la spesa al supermercato tra piu catene, copertura Lombardia e Sicilia.

## Funzionalita Implementate (v3.1.0 - 28 Marzo 2026)

### Core
- Auth (JWT), liste spesa, ottimizzazione prezzi, mappa Leaflet, PWA, referral, notifiche, condivisione familiare, password reset
- Scraping reale DoveConviene.it, 12 categorie, Gestione Prezzi multi-fonte
- 33 supermercati, ~7000 prodotti, 15 catene

### v3.1.0 - Offerte Geolocalizzate
- **Filtro geografico**: la pagina Offerte mostra solo supermercati nel raggio di 15km dalla posizione utente
- **Indicatore posizione**: "Catania, Sicilia — raggio 15 km" sotto il titolo
- **Distanza negozio**: ogni card mostra la distanza in km dal punto utente
- **Warning senza posizione**: banner per impostare la posizione dalla Home
- Catania: 7 negozi / 42 offerte. Pioltello: 12 negozi / 80 offerte.

### v3.0.0 - Click-to-Add + Product Tooltip
- Offerte cliccabili: tap aggiunge alla lista spesa
- Product Tooltip: hover mostra foto (Open Food Facts), marca, formato
- Quick List: localStorage bridge tra Offerte e Home

### v2.8.0 - Backend Refactoring
- server.py suddiviso in 13 file modulari

### v2.7.0 - Fuzzy Matching + Scraping Multi-Fonte
- Fuzzy Product Matching, Scraping DoveConviene + Pepesto API + Cross-Reference

## Architettura
- Backend: FastAPI modulare (routes/, models.py, dependencies.py)
- Frontend: React + TailwindCSS + Leaflet + Framer Motion
- Database: MongoDB (motor async)
- Immagini: Open Food Facts API + cache MongoDB

## Backlog
### P1: Missioni Giornaliere/Settimanali (gamification)
### P2: Integrazione Pepesto API
### P2: Espansione nazionale Q2 2026
### P3: Assistenti Vocali
