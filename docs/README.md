# Shopply - Spesa Intelligente

PWA per ottimizzare la spesa al supermercato. Trova i migliori prezzi tra 12 supermercati nella tua zona.

## Funzionalita

- Ottimizzazione spesa multi-supermercato
- Prezzi reali da DoveConviene.it (web scraping)
- 2500+ prodotti in 12 categorie
- 12 supermercati: Esselunga, Conad, Carrefour, Coop, Lidl, Eurospin, Aldi, MD, Penny, Despar, Unes, Iperal
- Mappa interattiva con percorsi
- Condivisione liste con la famiglia
- Programma referral con punti bonus
- Notifiche offerte in tempo reale
- Installabile come app (PWA)
- Funziona offline

## Deploy su GitHub Pages

Il frontend e nella cartella `docs/`. Per attivare GitHub Pages:

1. Vai su **Settings** > **Pages** nel repository
2. Sotto **Source**, seleziona **Deploy from a branch**
3. Seleziona branch `main` e cartella `/docs`
4. Salva

Il sito sara disponibile su: `https://filippodb.github.io/shopply-pwa/`

## Backend

Il backend FastAPI + MongoDB e hostato separatamente su Emergent Cloud.

## Stack

- **Frontend**: React.js, TailwindCSS, Framer Motion, Leaflet
- **Backend**: FastAPI, Python, MongoDB
- **Scraping**: BeautifulSoup (DoveConviene.it)
