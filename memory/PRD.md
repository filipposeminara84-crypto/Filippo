# Shopply v2.1 - Product Requirements Document

## Problema
Famiglie italiane spendono tempo confrontando volantini e pianificando la spesa settimanale.

## Soluzione
App web per ottimizzazione spesa multi-supermercato con aggiornamento prezzi automatico, condivisione familiare e programma referral.

## Target Audience
- Famiglie italiane area Pioltello/Segrate
- Utenti attenti al risparmio

## Tech Stack
- Frontend: React 19, TailwindCSS, Framer Motion, React-Leaflet
- Backend: FastAPI (Python)
- Database: MongoDB
- Mappe: Leaflet + OpenStreetMap
- Auth: JWT Email/Password

## v2.1 Features - Programma Referral ✅
### Sistema Referral
- [x] Codice referral univoco per utente (formato: ABC12XYZ)
- [x] Punti bonus: 50 punti per invitante, 25 punti per invitato
- [x] 10 punti = €1 di sconto
- [x] Dashboard referral con statistiche complete
- [x] Copia/condividi codice referral
- [x] Invito via email con tracking
- [x] Classifica Top Referrer
- [x] Riscatto punti come sconto
- [x] Pre-compilazione codice da URL (?ref=CODICE)
- [x] Notifiche per registrazioni e bonus

### v2.0 Features (precedenti)
- [x] Database espanso: 1477 prodotti, 7 supermercati, 12 categorie
- [x] Aggiornamento prezzi automatico con offerte
- [x] Sistema notifiche in-app
- [x] Condivisione liste familiari
- [x] Pagina offerte del giorno

### v1.0 MVP Features
- [x] Auth JWT email/password
- [x] Input lista spesa con autocomplete
- [x] Algoritmo ottimizzazione greedy
- [x] Mappa interattiva percorso
- [x] Storico ricerche
- [x] Impostazioni preferenze

## API Referral Program
- GET /api/referral/stats - Statistiche utente
- GET /api/referral/inviti - Lista inviti
- POST /api/referral/invita - Invia invito
- POST /api/referral/riscatta - Riscatta punti
- POST /api/referral/genera-codice - Genera codice per utenti esistenti
- GET /api/referral/classifica - Top 10 referrer

## Test Results v2.1
- Backend: 100% (22/22 endpoints)
- Frontend: 95%
- Integration: 100%

## Backlog P1
- [ ] Push notifications PWA
- [ ] Input vocale lista
- [ ] Scan barcode
- [ ] Web scraping prezzi reali
- [ ] Livelli VIP referral (Bronze/Silver/Gold)

## Dates
- 21/02/2026: MVP completato
- 21/02/2026: v2.0 (DB espanso, prezzi auto, notifiche, condivisione)
- 21/02/2026: v2.1 Programma Referral
