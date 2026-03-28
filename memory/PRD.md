# Shopply - PRD

## Problema Originale
App web per ottimizzare la spesa al supermercato tra piu catene, copertura Lombardia e Sicilia.

## Funzionalita Implementate (v2.9.0 - 28 Marzo 2026)

### Core
- Auth (JWT), liste spesa, ottimizzazione prezzi, mappa Leaflet, PWA, referral, notifiche, condivisione familiare, password reset
- Scraping reale DoveConviene.it, 12 categorie, pagina Gestione Prezzi multi-fonte
- 33 supermercati, ~7000 prodotti, 15 catene

### v2.9.0 - Product Tooltip con Immagini
- **Tooltip interattivo**: hover/tap su qualsiasi nome prodotto mostra foto reale, marca e formato
- **Open Food Facts API**: integrazione gratuita per immagini reali di prodotti italiani
- **Cache DB**: le immagini vengono salvate in MongoDB per velocizzare i successivi accessi
- **Backend**: nuovo endpoint GET /api/prodotti/immagine?q=nome_prodotto
- **Frontend**: nuovo componente ProductTooltip.js integrato in RisultatiPage

### v2.8.0 - Backend Refactoring
- server.py (1860 righe) suddiviso in 13 file modulari
- Zero regressioni (37 test backend + frontend)

### v2.7.0 - Fuzzy Matching + Scraping Multi-Fonte
- Fuzzy Product Matching (suffissi quantita: ml, l, g, kg, pz, conf)
- Scraping Multi-Fonte: DoveConviene, Pepesto API, Cross-Reference Engine

## Architettura Tecnica
- Backend: FastAPI modulare (routes/, models.py, dependencies.py)
- Frontend: React + TailwindCSS + Leaflet + Framer Motion
- Database: MongoDB (motor async driver)
- Scraping: httpx + BeautifulSoup4 (scraper.py)
- Immagini: Open Food Facts API + cache MongoDB
- PWA: Service Worker + manifest.json

## Backlog
### P1: Missioni Giornaliere/Settimanali (gamification)
### P2: Integrazione Pepesto API (chiave API a pagamento)
### P2: Espansione nazionale Q2 2026
### P3: Assistenti Vocali
