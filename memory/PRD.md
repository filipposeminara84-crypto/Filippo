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
- **Flusso "Password Dimenticata"**: Link nella pagina login, endpoint backend per richiesta/verifica/reset, pagina dedicata al reset
- **Correzione Geolocalizzazione**: enableHighAccuracy, timeout 10s, maximumAge 60s
- **Fix Build Frontend**: Rimosso codice JSX duplicato in LoginPage.js, corretta struttura ternario
- **Fix Import**: Corretto `@/` alias in index.js per compatibilità CRA build
- **Route Reset Password**: Aggiunta route /reset-password in App.js

## Schema DB Principale
- **utenti**: {id, email, nome, hashed_password, referral_code, punti_referral}
- **prodotti**: {id, nome_prodotto, supermercato_id, prezzo, categoria, in_offerta}
- **supermercati**: {id, nome, catena, indirizzo, lat, lng}
- **liste_spesa**: {id, utente_id, nome, prodotti}
- **notifiche**: {id, utente_id, tipo, messaggio}
- **famiglie**: {id, nome, creatore_id, membri}
- **password_resets**: {email, token, expiry, used}

## Backlog Prioritizzato

### P2 - Prossime
- Missioni Giornaliere/Settimanali (engagement gamification)

### P3 - Future
- Integrazione Assistenti Vocali (Google Assistant, Alexa, Siri)

## Note Tecniche
- Email reset password è SIMULATA (stampa in console + notifica in-app + demo_token in risposta)
- Backend monolitico in server.py (considerare suddivisione in moduli)
- Tutti i componenti UI in italiano
