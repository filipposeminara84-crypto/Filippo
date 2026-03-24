# Shopply - PRD (Product Requirements Document)

## Problema Originale
App web per ottimizzare la spesa al supermercato, trovando i migliori prezzi tra più supermercati nella zona dell'utente.

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

### V2.0
- Database espanso, aggiornamento automatico prezzi
- Notifiche in-app, condivisione liste familiari

### V2.1
- Programma referral, PWA installabile

### V2.2
- Flusso "Password Dimenticata", Fix Build Frontend

### V2.3
- 12 supermercati, scraping DoveConviene.it, pagina Gestione Prezzi

### V2.4
- Selettore posizione manuale, autocomplete migliorato, catalogo prodotti unici

### V2.5 (24 Marzo 2026)
- **"📍 Usa posizione attuale"**: Bottone GPS con reverse geocoding Nominatim che suggerisce via completa (es. "Via Roma, Gallarate", "Piazza Liberta, 1, Gallarate")
- **Ricerca indirizzi migliorata**: Risultati con via+civico+citta tramite addressdetails=1
- **Conferma indirizzo GPS**: Riquadro verde con indirizzo suggerito e bottone "Usa questo indirizzo"
- **File PWA GitHub Pages**: /app/docs/ pronti per deploy

## Backlog Prioritizzato

### P2 - Prossime
- Missioni Giornaliere/Settimanali

### P3 - Future
- Integrazione Assistenti Vocali

## Note Tecniche
- Geocoding: Nominatim/OpenStreetMap (gratuito, no API key)
- Scraping: DoveConviene.it reale con BeautifulSoup
- Email reset password simulata
- Backend monolitico in server.py
