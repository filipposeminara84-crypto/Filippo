# Shopply - PRD

## Problema Originale
App web per ottimizzare la spesa al supermercato tra piu catene, copertura Lombardia e Sicilia.

## Funzionalita Implementate (v2.6.1 - 27 Marzo 2026)

### Core
- Auth, liste spesa, ottimizzazione prezzi, mappa Leaflet, PWA, referral, notifiche, condivisione familiare, password reset
- Scraping reale da DoveConviene.it, 12 categorie, pagina Gestione Prezzi

### v2.6 - Espansione Lombardia + Sicilia
- 33 supermercati in 6 citta (Pioltello, Segrate, Cernusco, Gallarate, Catania, Palermo)
- 6963 prodotti con prezzi regionali
- Catene: Esselunga, Conad, Coop, Carrefour, Lidl, Eurospin, Aldi, MD, Penny, Despar, Unes, Iperal, Il Gigante, Deco, Ipercoop

### v2.6.1 - Fix Geolocalizzazione Forzata
- **Posizione salvata in localStorage**: La posizione manuale persiste tra sessioni
- **getUserLocation() condizionale**: GPS solo se nessuna posizione salvata
- **RisultatiPage.js fix**: Usa posizione da navigation state/localStorage (non piu hardcoded Pioltello)
- **userLocation passata a /risultati**: navigate() include userLocation nello state
- **LocationPicker con regioni**: Sezioni Lombardia e Sicilia + messaggio copertura

## API Principali
- Auth, Supermercati (getAll, nearby, copertura), Prodotti (filtri+paginazione, autocomplete, offerte, catalogo)
- Scraper (run, status, log, categories, search-preview), Liste, Ottimizzazione

## Backlog
### P2
- Missioni Giornaliere/Settimanali
### P3
- Integrazione Assistenti Vocali
- Espansione nazionale Q2 2026
