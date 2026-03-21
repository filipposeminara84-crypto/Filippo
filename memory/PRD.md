# Shopply - PRD (Product Requirements Document)

## Problema Originale
App web per ottimizzare la spesa al supermercato, trovando i migliori prezzi tra più supermercati nella zona dell'utente (Area Pioltello).

## Stack Tecnologico
- **Frontend**: React.js, TailwindCSS, Framer Motion, Leaflet, lucide-react
- **Backend**: FastAPI, Python, MongoDB (motor), JWT auth
- **Architettura**: SPA con REST API, PWA con offline capabilities

## Funzionalità Implementate

### MVP (v1.0)
- Autenticazione utente (email/password)
- Creazione e gestione liste della spesa
- Algoritmo di ottimizzazione prezzi
- Mappa con posizioni supermercati e percorsi
- Dati seed per supermercati e prodotti

### V2.0
- Database prodotti/supermercati espanso
- Aggiornamento automatico prezzi + offerte speciali
- Notifiche in-app per offerte
- Condivisione liste con familiari

### V2.1
- Programma referral (punti/sconti per inviti)
- PWA installabile con supporto offline

### V2.2 (18 Marzo 2026)
- Flusso "Password Dimenticata" completo
- Fix Build Frontend (JSX duplicato)

### V2.3 (21 Marzo 2026)
- 12 Supermercati con scraping prezzi reali da DoveConviene.it
- 2532 prodotti in 12 categorie
- Pagina Gestione Prezzi (/prezzi)

### V2.4 (21 Marzo 2026) - Fix Geolocalizzazione e Catalogo
- **Selettore Posizione Manuale**: Modal con GPS, ricerca indirizzo (Nominatim/OpenStreetMap), 10 localita preimpostate (Pioltello, Segrate, Cernusco, Rodano, Vignate, Pantigliate, Limito, Milano-Lambrate, Vimodrone)
- **Autocomplete migliorato**: Da 1 a 20 risultati, ricerca 'contains' invece di 'startsWith'
- **Endpoint /api/catalogo**: 210 prodotti unici con prezzo_min, prezzo_max, num_supermercati (aggregazione MongoDB)
- **Paginazione prodotti**: Endpoint /api/prodotti con limit fino a 1000 e skip
- **Barra posizione**: Visibile nella home page con nome localita e coordinate

## Schema DB Principale
- **utenti**: {id, email, nome, hashed_password, referral_code, punti_referral}
- **prodotti**: {id, nome_prodotto, supermercato_id, prezzo, categoria, in_offerta, fonte_prezzo, data_aggiornamento}
- **supermercati**: {id, nome, catena, indirizzo, lat, lng}
- **liste_spesa**: {id, utente_id, nome, prodotti}
- **notifiche**: {id, utente_id, tipo, messaggio}
- **famiglie**: {id, nome, creatore_id, membri}
- **scraping_log**: {id, data, prodotti_trovati, prodotti_aggiornati, nuove_offerte, errori, tipo}

## Backlog Prioritizzato

### P2 - Prossime
- Missioni Giornaliere/Settimanali (engagement gamification)

### P3 - Future
- Integrazione Assistenti Vocali (Google Assistant, Alexa, Siri) - rinviata in attesa delle API

## Note Tecniche
- Email reset password simulata (console + notifica in-app)
- Scraping DoveConviene.it reale (non simulato)
- Geocoding via Nominatim (OpenStreetMap) - gratuito, no API key
- Backend monolitico in server.py
- File PWA per GitHub Pages in /app/docs/
