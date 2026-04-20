# Shopply - PRD

## Problema Originale
App web per ottimizzare la spesa al supermercato tra piu catene, copertura Lombardia e Sicilia.

## Funzionalita Implementate (v3.0.0 - 28 Marzo 2026)

### Core
- Auth (JWT), liste spesa, ottimizzazione prezzi, mappa Leaflet, PWA, referral, notifiche, condivisione familiare, password reset
- Scraping reale DoveConviene.it, 12 categorie, Gestione Prezzi multi-fonte
- 33 supermercati, ~7000 prodotti, 15 catene

### v3.0.0 - Click-to-Add dalle Offerte + Product Tooltip
- **Offerte cliccabili**: tap/click su un prodotto in offerta lo aggiunge alla lista della spesa
- **Stato visivo**: bordo verde + checkmark per prodotti aggiunti, tappabile per rimuovere
- **Contatore lista**: badge "Lista (N)" linkato alla Home per procedere all'ottimizzazione
- **Quick List**: prodotti salvati in localStorage, caricati automaticamente in HomePage
- **Product Tooltip**: hover/tap mostra foto reale (Open Food Facts), marca e formato
- **Toast notifica**: conferma visiva "Prodotto aggiunto alla lista"

### v2.8.0 - Backend Refactoring
- server.py suddiviso in 13 file modulari, zero regressioni

### v2.7.0 - Fuzzy Matching + Scraping Multi-Fonte
- Fuzzy Product Matching, Scraping DoveConviene + Pepesto API + Cross-Reference

## Architettura
- Backend: FastAPI modulare (routes/, models.py, dependencies.py)
- Frontend: React + TailwindCSS + Leaflet + Framer Motion
- Database: MongoDB (motor async)
- Immagini: Open Food Facts API + cache MongoDB
- PWA: Service Worker + manifest.json

## Backlog
### P1: Missioni Giornaliere/Settimanali (gamification)
### P2: Integrazione Pepesto API
### P2: Espansione nazionale Q2 2026
### P3: Assistenti Vocali
