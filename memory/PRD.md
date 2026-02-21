# Shopply - Product Requirements Document

## Problema
Famiglie italiane spendono tempo significativo confrontando volantini e pianificando percorsi per la spesa settimanale in modo manuale e inefficiente.

## Soluzione
Shopply è un'app web che ottimizza la spesa multi-supermercato, bilanciando prezzo e tempo di percorrenza.

## Target Audience
- Famiglie italiane (area Pioltello MVP)
- Utenti attenti al risparmio
- Chi fa la spesa fisica settimanale

## Tech Stack
- **Frontend:** React 19, TailwindCSS, Framer Motion
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Mappe:** Leaflet + OpenStreetMap
- **Auth:** JWT Email/Password

## Core Features Implementate (MVP)
- [x] Autenticazione JWT (registrazione/login)
- [x] Input lista spesa con autocomplete (280+ prodotti)
- [x] Salvataggio liste preferite (max 5)
- [x] Algoritmo ottimizzazione greedy (prezzo + tempo)
- [x] Parametri personalizzabili (raggio, max supermercati, peso prezzo/tempo)
- [x] Mappa interattiva con percorso ottimizzato
- [x] Bottone "Avvia Navigazione" (Google Maps)
- [x] Storico ultime 10 ricerche
- [x] Statistiche personali (risparmio totale)
- [x] Design responsive mobile-first

## Database Seed
- 5 supermercati area Pioltello (Coop, Esselunga, Lidl, Eurospin, Carrefour)
- 280 prodotti con prezzi variabili per negozio
- Categorie: Latticini, Pane/Cereali, Frutta/Verdura, Carne/Pesce, Bevande, Snack/Dolci, Igiene/Casa

## API Endpoints
- POST /api/auth/register, /api/auth/login
- GET /api/auth/me
- GET/PUT /api/preferenze
- GET /api/supermercati, /api/prodotti
- GET /api/prodotti/autocomplete
- GET/POST/DELETE /api/liste
- POST /api/ottimizza
- GET /api/storico
- PATCH /api/storico/{id}/eseguita
- POST /api/matrice-prezzi

## Backlog P1 (Post-MVP)
- [ ] Input vocale lista spesa
- [ ] Scan barcode prodotti
- [ ] Notifiche push offerte
- [ ] Integrazione programmi fedeltà
- [ ] Condivisione lista con familiari
- [ ] Modalità offline (cache)
- [ ] Espansione database prodotti
- [ ] Suggerimenti AI prodotti simili

## Date
- **21/02/2026:** MVP completato e testato
