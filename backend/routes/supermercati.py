"""Supermarket and product routes."""
import math
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from models import Supermercato, Prodotto, Preferenze
from database import db
from dependencies import get_current_user, haversine_distance
from store_discovery import discover_stores_overpass
from catalog_generator import generate_base_catalog, import_scraped_offers

logger = logging.getLogger(__name__)
router = APIRouter(tags=["supermercati-prodotti"])


# ============== PREFERENZE ==============

@router.get("/preferenze", response_model=Preferenze)
async def get_preferenze(current_user: dict = Depends(get_current_user)):
    return Preferenze(**current_user["preferenze"])

@router.put("/preferenze", response_model=Preferenze)
async def update_preferenze(prefs: Preferenze, current_user: dict = Depends(get_current_user)):
    await db.utenti.update_one({"id": current_user["id"]}, {"$set": {"preferenze": prefs.model_dump()}})
    return prefs


# ============== SUPERMERCATI ==============

@router.get("/supermercati", response_model=List[Supermercato])
async def get_supermercati():
    return await db.supermercati.find({}, {"_id": 0}).to_list(200)

@router.get("/supermercati/nearby")
async def get_supermercati_nearby(lat: float, lng: float, raggio_km: float = 10):
    supermercati = await db.supermercati.find({}, {"_id": 0}).to_list(2000)

    risultati = []
    for sup in supermercati:
        dist = haversine_distance(lat, lng, sup["lat"], sup["lng"])
        if dist <= raggio_km:
            sup["distanza_km"] = round(dist, 1)
            risultati.append(sup)

    # If we have OSM (real) stores in the area, use only those
    osm_in_area = [s for s in risultati if s.get("fonte") == "osm"]
    if osm_in_area:
        risultati = osm_in_area

    risultati.sort(key=lambda x: x["distanza_km"])
    return risultati


@router.post("/supermercati/discover")
async def discover_supermercati(
    lat: float, lng: float, raggio_km: float = 15,
    background_tasks: BackgroundTasks = None,
):
    """Discover real supermarkets from OpenStreetMap and store them in DB."""
    from pymongo import UpdateOne

    # Check cache: if we already discovered stores near this point recently
    cache_key = f"{round(lat, 2)}_{round(lng, 2)}"
    cache = await db.discovery_cache.find_one({"key": cache_key}, {"_id": 0})
    if cache:
        cached_at = cache.get("timestamp", "")
        try:
            cached_dt = datetime.fromisoformat(cached_at.replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - cached_dt).days < 7:
                # Return cached stores
                stores = await db.supermercati.find(
                    {"fonte": "osm"}, {"_id": 0}
                ).to_list(2000)
                nearby = []
                for s in stores:
                    d = haversine_distance(lat, lng, s["lat"], s["lng"])
                    if d <= raggio_km:
                        s["distanza_km"] = round(d, 1)
                        nearby.append(s)
                nearby.sort(key=lambda x: x["distanza_km"])

                # Ensure catalog exists for these stores
                try:
                    await generate_base_catalog(db, nearby)
                except Exception:
                    pass

                return {
                    "source": "cache",
                    "stores": len(nearby),
                    "supermercati": nearby,
                }
        except Exception:
            pass

    # Discover from Overpass API
    osm_stores = await discover_stores_overpass(lat, lng, int(raggio_km * 1000))
    if not osm_stores:
        return {"source": "overpass", "stores": 0, "supermercati": [], "error": "Nessun risultato da OpenStreetMap"}

    # Upsert discovered stores in DB
    ops = []
    for store in osm_stores:
        ops.append(UpdateOne(
            {"id": store["id"]},
            {"$set": store},
            upsert=True,
        ))
    if ops:
        await db.supermercati.bulk_write(ops)

    # Update cache
    await db.discovery_cache.update_one(
        {"key": cache_key},
        {"$set": {"key": cache_key, "timestamp": datetime.now(timezone.utc).isoformat(), "lat": lat, "lng": lng, "count": len(osm_stores)}},
        upsert=True,
    )

    # Generate base catalog for new stores SYNCHRONOUSLY (fast)
    try:
        n = await generate_base_catalog(db, osm_stores)
        logger.info(f"[Discover] Generated {n} base products for new stores")
    except Exception as e:
        logger.error(f"[Discover] Catalog generation error: {e}")

    # Start DoveConviene scraping in BACKGROUND (slow)
    if background_tasks:
        background_tasks.add_task(_background_scrape_offers, osm_stores)

    # Calculate distances and return
    result = []
    for s in osm_stores:
        d = haversine_distance(lat, lng, s["lat"], s["lng"])
        if d <= raggio_km:
            s["distanza_km"] = round(d, 1)
            result.append(s)
    result.sort(key=lambda x: x["distanza_km"])

    # Index for performance
    await db.supermercati.create_index("id")
    await db.supermercati.create_index("fonte")
    await db.prodotti.create_index("supermercato_id")

    return {
        "source": "overpass",
        "stores": len(result),
        "chains": sorted(set(s["catena"] for s in result)),
        "supermercati": result,
    }


async def _background_scrape_offers(stores: list):
    """Background task: scrape DoveConviene for real offers — full category coverage."""
    try:
        from scraper import scrape_doveconviene
        # Extended list: 40+ terms covering all major grocery categories
        scrape_terms = [
            # Latticini
            "latte", "yogurt", "mozzarella", "parmigiano", "burro", "ricotta", "gorgonzola", "philadelphia",
            # Pane e Cereali
            "pasta", "riso", "farina", "pane", "cereali", "crackers", "fette-biscottate",
            # Frutta e Verdura
            "mele", "banane", "arance", "pomodori", "insalata", "patate", "carote",
            # Carne e Pesce
            "pollo", "macinato", "prosciutto", "salmone", "tonno", "bresaola",
            # Bevande
            "acqua", "coca-cola", "succo", "birra", "caffe", "fanta",
            # Snack e Dolci
            "biscotti", "nutella", "cioccolato", "patatine", "gelato",
            # Condimenti e Salse
            "olio-extravergine", "passata-pomodoro", "pesto", "maionese",
            # Surgelati
            "pizza-surgelata", "minestrone", "patate-fritte",
            # Igiene e Casa
            "carta-igienica", "detersivo", "ammorbidente", "scottex",
            # Igiene Personale
            "shampoo", "bagnoschiuma", "dentifricio", "deodorante",
            # Baby e Pet
            "pannolini", "crocchette-cane",
        ]
        all_scraped = []
        for term in scrape_terms:
            try:
                results = await scrape_doveconviene(term)
                all_scraped.extend(results)
                if results:
                    logger.info(f"[BG] DoveConviene '{term}': {len(results)} results")
            except Exception as e:
                logger.warning(f"[BG] DoveConviene '{term}' failed: {e}")
            await asyncio.sleep(1.5)

        if all_scraped:
            stats = await import_scraped_offers(db, all_scraped, stores)
            logger.info(f"[BG] Imported scraped offers: {stats}")

        # Record scraping event
        await db.scraping_log.insert_one({
            "id": str(uuid.uuid4()) if 'uuid' in dir() else "bg-scrape",
            "data": datetime.now(timezone.utc).isoformat(),
            "prodotti_trovati": len(all_scraped),
            "tipo": "background_discovery",
            "fonti": ["doveconviene"],
        })
    except Exception as e:
        logger.error(f"[BG] Scraping error: {e}")


@router.post("/supermercati/scrape-offerte")
async def trigger_scrape_offerte(
    lat: float, lng: float, raggio_km: float = 15,
    background_tasks: BackgroundTasks = None,
):
    """Manually trigger DoveConviene scraping for stores near a location."""
    stores = await db.supermercati.find({"fonte": "osm"}, {"_id": 0}).to_list(2000)
    nearby = [s for s in stores if haversine_distance(lat, lng, s["lat"], s["lng"]) <= raggio_km]

    if not nearby:
        return {"message": "Nessun negozio scoperto in zona. Esegui prima /api/supermercati/discover"}

    if background_tasks:
        background_tasks.add_task(_background_scrape_offers, nearby)

    chains = sorted(set(s["catena"] for s in nearby))
    return {
        "message": f"Scraping avviato per {len(nearby)} negozi ({len(chains)} catene)",
        "stores": len(nearby),
        "chains": chains,
    }

@router.get("/copertura")
async def get_copertura():
    supermercati = await db.supermercati.find({}, {"_id": 0, "regione": 1, "citta": 1, "catena": 1}).to_list(200)
    regioni = {}
    for s in supermercati:
        reg = s.get("regione", "Altro")
        citta = s.get("citta", "N/D")
        if reg not in regioni:
            regioni[reg] = {}
        if citta not in regioni[reg]:
            regioni[reg][citta] = set()
        regioni[reg][citta].add(s["catena"])
    copertura = []
    for reg, citta_dict in regioni.items():
        for citta, catene in citta_dict.items():
            copertura.append({
                "regione": reg, "citta": citta, "catene": sorted(list(catene)),
                "num_negozi": sum(1 for s in supermercati if s.get("citta") == citta),
            })
    return {"zone_coperte": copertura, "totale_negozi": len(supermercati),
            "regioni": sorted(list(regioni.keys())),
            "messaggio": "Copertura Lombardia e Sicilia. Espansione nazionale prevista Q2 2026."}

@router.get("/supermercati/{supermercato_id}", response_model=Supermercato)
async def get_supermercato(supermercato_id: str):
    sup = await db.supermercati.find_one({"id": supermercato_id}, {"_id": 0})
    if not sup:
        raise HTTPException(status_code=404, detail="Supermercato non trovato")
    return sup


# ============== PRODOTTI ==============

@router.get("/prodotti", response_model=List[Prodotto])
async def get_prodotti(categoria: Optional[str] = None, search: Optional[str] = None,
                       in_offerta: Optional[bool] = None, supermercato_id: Optional[str] = None,
                       limit: int = 500, skip: int = 0):
    query = {}
    if categoria:
        query["categoria"] = categoria
    if search:
        query["nome_prodotto"] = {"$regex": search, "$options": "i"}
    if in_offerta:
        query["in_offerta"] = True
    if supermercato_id:
        query["supermercato_id"] = supermercato_id
    return await db.prodotti.find(
        query,
        {"_id": 0, "id": 1, "nome_prodotto": 1, "categoria": 1, "brand": 1, "formato": 1,
         "supermercato_id": 1, "prezzo": 1, "in_offerta": 1, "sconto_percentuale": 1, "data_aggiornamento": 1}
    ).skip(skip).limit(min(limit, 1000)).to_list(min(limit, 1000))

@router.get("/prodotti/autocomplete")
async def autocomplete_prodotti(q: str):
    if len(q) < 2:
        return []
    prodotti = await db.prodotti.find(
        {"nome_prodotto": {"$regex": q, "$options": "i"}}, {"_id": 0, "nome_prodotto": 1}
    ).to_list(100)
    nomi_unici = sorted(set(p["nome_prodotto"] for p in prodotti))
    return nomi_unici[:20]

@router.get("/prodotti/offerte")
async def get_offerte():
    offerte = await db.prodotti.find(
        {"in_offerta": True},
        {"_id": 0, "nome_prodotto": 1, "categoria": 1, "brand": 1, "formato": 1,
         "supermercato_id": 1, "prezzo": 1, "prezzo_precedente": 1, "sconto_percentuale": 1}
    ).limit(200).to_list(200)
    by_store = {}
    for p in offerte:
        store_id = p["supermercato_id"]
        if store_id not in by_store:
            by_store[store_id] = []
        by_store[store_id].append(p)
    return by_store

@router.get("/categorie")
async def get_categorie():
    return await db.prodotti.distinct("categoria")

@router.get("/catalogo")
async def get_catalogo(categoria: Optional[str] = None):
    query = {}
    if categoria:
        query["categoria"] = categoria
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {"nome": "$nome_prodotto", "categoria": "$categoria"},
            "brand": {"$first": "$brand"}, "formato": {"$first": "$formato"},
            "prezzo_min": {"$min": "$prezzo"}, "prezzo_max": {"$max": "$prezzo"},
            "num_supermercati": {"$sum": 1},
            "in_offerta": {"$max": {"$cond": ["$in_offerta", 1, 0]}}
        }},
        {"$project": {"_id": 0, "nome_prodotto": "$_id.nome", "categoria": "$_id.categoria",
                       "brand": 1, "formato": 1, "prezzo_min": 1, "prezzo_max": 1,
                       "num_supermercati": 1, "in_offerta": {"$gt": ["$in_offerta", 0]}}},
        {"$sort": {"categoria": 1, "nome_prodotto": 1}}
    ]
    return await db.prodotti.aggregate(pipeline).to_list(500)
