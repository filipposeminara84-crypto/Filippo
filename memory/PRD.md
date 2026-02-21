# Shopply v2.0 - Product Requirements Document

## Problema
Famiglie italiane spendono tempo significativo confrontando volantini e pianificando percorsi per la spesa settimanale.

## Soluzione
App web per ottimizzazione spesa multi-supermercato con aggiornamento prezzi automatico e condivisione familiare.

## Target Audience
- Famiglie italiane area Pioltello/Segrate
- Utenti attenti al risparmio
- Chi fa la spesa fisica settimanale

## Tech Stack
- **Frontend:** React 19, TailwindCSS, Framer Motion, React-Leaflet
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Mappe:** Leaflet + OpenStreetMap
- **Auth:** JWT Email/Password

## v2.0 Features Implementate
### Database Espanso
- [x] 7 supermercati (Coop, Esselunga, Lidl, Eurospin, Carrefour, Penny, MD)
- [x] 1477 prodotti con prezzi realistici
- [x] 12 categorie merceologiche

### Aggiornamento Prezzi Automatico
- [x] Sistema variazione prezzi (-5% a +3%)
- [x] Generazione automatica offerte (10-30% sconto)
- [x] Tracking prezzo precedente
- [x] API /api/prezzi/aggiorna (background task)

### Sistema Notifiche
- [x] Notifiche in-app per offerte personalizzate
- [x] Notifiche condivisione liste
- [x] Badge contatore non lette
- [x] Dropdown notifiche con azioni

### Condivisione Liste Familiari
- [x] Condivisione via email
- [x] Liste condivise visibili a tutti i membri
- [x] Indicatore liste condivise
- [x] Rimozione condivisione

### Pagina Offerte
- [x] Visualizzazione prodotti in sconto
- [x] Filtri per categoria
- [x] Prezzi barrati con nuovo prezzo
- [x] Pulsante aggiorna prezzi

## API Endpoints v2.0
- POST /api/prezzi/aggiorna
- GET /api/prezzi/ultimo-aggiornamento
- GET /api/prodotti/offerte
- GET/POST/PATCH/DELETE /api/notifiche
- POST /api/liste/{id}/condividi
- DELETE /api/liste/{id}/condividi/{email}
- POST /api/famiglia/crea
- POST /api/famiglia/invita
- GET /api/famiglia/inviti
- POST /api/famiglia/inviti/{id}/accetta

## Test Results
- Backend: 100% (22/22 endpoints)
- Frontend: 90%
- Integration: 95%

## Backlog P1 (Future)
- [ ] Input vocale lista spesa
- [ ] Scan barcode prodotti
- [ ] Push notifications (PWA)
- [ ] Integrazione programmi fedeltà
- [ ] Modalità offline (cache)
- [ ] Web scraping prezzi reali
- [ ] AI suggerimenti prodotti simili

## Dates
- **21/02/2026:** MVP completato
- **21/02/2026:** v2.0 con espansione DB, aggiornamento prezzi, notifiche, condivisione
