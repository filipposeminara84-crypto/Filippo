# Shopply v2.1 - Product Requirements Document

## Status: ✅ DEPLOYMENT READY

## Problema
Famiglie italiane spendono tempo confrontando volantini e pianificando la spesa settimanale.

## Soluzione
App web per ottimizzazione spesa multi-supermercato con aggiornamento prezzi automatico, condivisione familiare e programma referral.

## Tech Stack
- Frontend: React 19, TailwindCSS, Framer Motion, React-Leaflet
- Backend: FastAPI (Python)
- Database: MongoDB
- Mappe: Leaflet + OpenStreetMap
- Auth: JWT Email/Password

## Features Implementate
### v2.1 - Programma Referral
- [x] Codice referral univoco per utente
- [x] Bonus: 50 punti invitante, 25 punti invitato
- [x] 10 punti = €1 sconto riscattabile
- [x] Dashboard referral completa
- [x] Classifica Top Referrer
- [x] Pre-compilazione codice da URL

### v2.0 - Espansione
- [x] 1477 prodotti, 7 supermercati, 12 categorie
- [x] Aggiornamento prezzi automatico (bulk write ottimizzato)
- [x] Sistema notifiche in-app
- [x] Condivisione liste familiari
- [x] Pagina offerte del giorno

### v1.0 - MVP
- [x] Auth JWT email/password
- [x] Input lista spesa con autocomplete
- [x] Algoritmo ottimizzazione greedy
- [x] Mappa interattiva percorso
- [x] Storico ricerche
- [x] Impostazioni preferenze

## Deployment Checks ✅
- [x] No hardcoded URLs/secrets
- [x] Environment variables configured
- [x] Query optimizations applied
- [x] Database indexes configured
- [x] CORS properly set
- [x] Supervisor config valid

## Backlog P1 (Future)
- [ ] Integrazione assistenti vocali (Google/Alexa/Siri) - richiede API keys
- [ ] Push notifications PWA
- [ ] Input vocale lista
- [ ] Scan barcode
- [ ] Web scraping prezzi reali
- [ ] Livelli VIP referral

## Test Results
- Backend: 100%
- Frontend: 95%
- Integration: 100%
- Deployment: READY

## Dates
- 21/02/2026: MVP
- 21/02/2026: v2.0 
- 21/02/2026: v2.1 + Deployment Ready
