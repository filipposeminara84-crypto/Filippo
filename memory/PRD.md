# Shopply - PRD

## Problema Originale
App web per ottimizzare la spesa al supermercato tra piu catene, copertura Lombardia e Sicilia.

## Funzionalita Implementate (v2.6.2 - 28 Marzo 2026)

### Core
- Auth, liste spesa, ottimizzazione prezzi, mappa Leaflet, PWA, referral, notifiche, condivisione familiare, password reset
- Scraping reale DoveConviene.it, 12 categorie, pagina Gestione Prezzi
- 33 supermercati, 6963 prodotti, 15 catene

### v2.6.2 - Fix Geolocalizzazione per Utenti Remoti
- **LocationPicker auto-open**: Se GPS negato/non disponibile, si apre automaticamente
- **Reverse geocoding su GPS**: GPS → via completa (es. "Via Etnea, Catania")
- **Persistenza localStorage**: Posizione manuale sopravvive a refresh/navigazione
- **Barra posizione con stato**: Arancione pulsante "Imposta" se non configurata, verde se OK
- **RisultatiPage con posizione dinamica**: Mappa centrata sulla posizione reale utente
- **Flusso testato**: Catania (GPS negato) → LocationPicker → seleziona → ottimizza → mappa Catania con negozi locali

## Copertura
| Regione | Citta | Negozi | Catene |
|---------|-------|--------|--------|
| Lombardia | Pioltello/Segrate/Cernusco | 12 | Coop, Esselunga, Lidl, Eurospin, Carrefour, Penny, Conad, Aldi, Despar, Unes, Iperal, MD |
| Lombardia | Gallarate | 9 | Esselunga x2, Conad, Coop, Carrefour, Lidl, Iperal, Il Gigante, MD |
| Sicilia | Catania | 7 | Conad x2, Deco x2, Eurospin, Lidl, Ipercoop |
| Sicilia | Palermo | 5 | Conad, Deco, Eurospin, Lidl, Ipercoop |

## Backlog
### P2: Missioni Giornaliere/Settimanali
### P3: Assistenti Vocali, Espansione nazionale Q2 2026
