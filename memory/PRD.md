# Shopply - PRD

## Problema Originale
App web per ottimizzare la spesa al supermercato tra piu catene, copertura Lombardia e Sicilia.

## Funzionalita Implementate (v2.7.0 - 28 Marzo 2026)

### Core
- Auth, liste spesa, ottimizzazione prezzi, mappa Leaflet, PWA, referral, notifiche, condivisione familiare, password reset
- Scraping reale DoveConviene.it, 12 categorie, pagina Gestione Prezzi multi-fonte
- 33 supermercati, 6963 prodotti, 15 catene

### v2.7.0 - Fuzzy Matching + Scraping Multi-Fonte
- **Fuzzy Product Matching**: L'algoritmo di ottimizzazione ora gestisce variazioni nei nomi dei prodotti (es. "Olio Extravergine 1L" matcha "Olio Extravergine" nel DB). Supporta suffissi quantita: ml, l, lt, cl, g, gr, kg, pz, pezzi, conf, confezione
- **Strategie di matching**: exact > normalized-exact > starts-with > contains > word-overlap
- **Scraping Multi-Fonte**: Architettura modulare con 3 fonti: DoveConviene (primaria), Pepesto API (opzionale, richiede PEPESTO_API_KEY), Cross-Reference Engine (analisi dati esistenti)
- **UI Gestione Prezzi aggiornata**: Toggle per attivare/disattivare fonti, badge colorati per fonte su ogni risultato, contatore fonti attive
- **Matrice prezzi**: Anche il confronto prezzi usa fuzzy matching

### v2.6.2 - Fix Geolocalizzazione per Utenti Remoti
- LocationPicker auto-open, reverse geocoding GPS, persistenza localStorage
- Barra posizione con stato, RisultatiPage con posizione dinamica

## Copertura
| Regione | Citta | Negozi | Catene |
|---------|-------|--------|--------|
| Lombardia | Pioltello/Segrate/Cernusco | 12 | Coop, Esselunga, Lidl, Eurospin, Carrefour, Penny, Conad, Aldi, Despar, Unes, Iperal, MD |
| Lombardia | Gallarate | 9 | Esselunga x2, Conad, Coop, Carrefour, Lidl, Iperal, Il Gigante, MD |
| Sicilia | Catania | 7 | Conad x2, Deco x2, Eurospin, Lidl, Ipercoop |
| Sicilia | Palermo | 5 | Conad, Deco, Eurospin, Lidl, Ipercoop |

## Architettura Tecnica
- Backend: FastAPI monolitico (server.py ~1860 righe)
- Frontend: React + TailwindCSS + Leaflet + Framer Motion
- Database: MongoDB (motor async driver)
- Scraping: httpx + BeautifulSoup4 (scraper.py)
- PWA: Service Worker + manifest.json
- Deploy GitHub Pages: /app/docs/

## Backlog
### P1: Refactoring server.py (monolite -> moduli routes/models/services)
### P2: Missioni Giornaliere/Settimanali (gamification)
### P2: Integrazione Pepesto API (richiede chiave API a pagamento)
### P3: Assistenti Vocali, Espansione nazionale Q2 2026
