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
- Correzione Geolocalizzazione (enableHighAccuracy)
- Fix Build Frontend (JSX duplicato)

### V2.3 (21 Marzo 2026) - Database Prodotti/Offerte
- **12 Supermercati**: Coop, Esselunga, Lidl, Eurospin, Carrefour, Penny, MD, Conad, Aldi, Despar, Unes, Iperal (tutti nell'area Pioltello/Segrate/Cernusco)
- **2532 Prodotti** suddivisi in 12 categorie (Latticini, Pane e Cereali, Frutta e Verdura, Carne e Pesce, Bevande, Snack e Dolci, Condimenti e Salse, Surgelati, Igiene e Casa, Igiene Personale, Baby e Infanzia, Pet Food)
- **Scraping Prezzi Reali da DoveConviene.it**: Sistema di web scraping con BeautifulSoup che estrae prezzi, offerte e sconti dai volantini
- **Pagina Gestione Prezzi** (/prezzi): Interfaccia per cercare prodotti, avviare scraping per categoria o termine, visualizzare anteprime prezzi e storico aggiornamenti
- **Aggiornamento prezzi in background**: Lo scraping viene eseguito in background con polling dello stato

## Schema DB Principale
- **utenti**: {id, email, nome, hashed_password, referral_code, punti_referral}
- **prodotti**: {id, nome_prodotto, supermercato_id, prezzo, categoria, in_offerta, fonte_prezzo, data_aggiornamento}
- **supermercati**: {id, nome, catena, indirizzo, lat, lng}
- **liste_spesa**: {id, utente_id, nome, prodotti}
- **notifiche**: {id, utente_id, tipo, messaggio}
- **famiglie**: {id, nome, creatore_id, membri}
- **password_resets**: {email, token, expiry, used}
- **scraping_log**: {id, data, prodotti_trovati, prodotti_aggiornati, nuove_offerte, errori, tipo}

## API Principali
- Auth: /api/auth/login, /api/auth/register, /api/auth/forgot-password, /api/auth/reset-password
- Prodotti: /api/prodotti, /api/prodotti/offerte, /api/prodotti/autocomplete
- Supermercati: /api/supermercati
- Scraper: /api/scraper/run, /api/scraper/status, /api/scraper/log, /api/scraper/categories, /api/scraper/search-preview
- Liste: /api/liste, /api/liste/{id}
- Ottimizzazione: /api/ottimizza

## Backlog Prioritizzato

### P2 - Prossime
- Missioni Giornaliere/Settimanali (engagement gamification)

### P3 - Future
- Integrazione Assistenti Vocali (Google Assistant, Alexa, Siri) - rinviata in attesa delle API

## Note Tecniche
- Email reset password è SIMULATA (stampa in console + notifica in-app)
- Backend monolitico in server.py (considerare suddivisione)
- Lo scraping da DoveConviene è REALE, non simulato
- Il database prodotti ha variazioni di prezzo realistiche per catena
