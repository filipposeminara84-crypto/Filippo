"""Scraper routes."""
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from database import db
from dependencies import get_current_user
from scraper import (
    scrape_doveconviene, scrape_all_categories, update_prices_from_scraping,
    scrape_product_multi, cross_reference_prices,
    SEARCH_TERMS, SOURCES,
)

router = APIRouter(prefix="/scraper", tags=["scraper"])

scraping_status = {
    "in_corso": False,
    "ultimo_scraping": None,
    "risultato": None,
    "log": [],
}


@router.post("/run")
async def run_scraper(background_tasks: BackgroundTasks, search_term: Optional[str] = None,
                      fonti: Optional[List[str]] = None, user=Depends(get_current_user)):
    if scraping_status["in_corso"]:
        raise HTTPException(status_code=409, detail="Scraping gia in corso")
    active_sources = fonti or list(SOURCES.keys())

    async def do_scraping():
        scraping_status["in_corso"] = True
        scraping_status["log"] = []
        try:
            scraping_status["log"].append(f"Fonti attive: {', '.join(active_sources)}")
            if search_term:
                scraping_status["log"].append(f"Scraping prodotto: {search_term}")
                results = await scrape_product_multi(search_term, active_sources)
                scraping_status["log"].append(f"Trovati {len(results)} risultati per '{search_term}'")
                by_source = {}
                for r in results:
                    src = r.get("fonte", "unknown")
                    by_source[src] = by_source.get(src, 0) + 1
                for src, count in by_source.items():
                    scraping_status["log"].append(f"  {src}: {count} prodotti")
            else:
                scraping_status["log"].append("Scraping completo di tutte le categorie...")
                data = await scrape_all_categories(active_sources)
                results = []
                for cat, items in data["categorie"].items():
                    results.extend(items)
                    scraping_status["log"].append(f"  {cat}: {len(items)} prodotti")

            supermercati = await db.supermercati.find({}, {"_id": 0}).to_list(100)
            update_result = await update_prices_from_scraping(db, results, supermercati)
            log_entry = {
                "id": str(uuid.uuid4()), "data": datetime.now(timezone.utc).isoformat(),
                "prodotti_trovati": len(results), "prodotti_aggiornati": update_result["prodotti_aggiornati"],
                "nuove_offerte": update_result["nuove_offerte"], "errori": update_result["errori"],
                "tipo": "singolo" if search_term else "completo", "search_term": search_term,
                "fonti": active_sources,
            }
            await db.scraping_log.insert_one({**log_entry})
            scraping_status["risultato"] = log_entry
            scraping_status["log"].append(
                f"Completato: {update_result['prodotti_aggiornati']} prezzi aggiornati, {update_result['nuove_offerte']} nuove offerte")
        except Exception as e:
            scraping_status["log"].append(f"Errore: {str(e)}")
            scraping_status["risultato"] = {"errore": str(e)}
        finally:
            scraping_status["in_corso"] = False
            scraping_status["ultimo_scraping"] = datetime.now(timezone.utc).isoformat()

    background_tasks.add_task(do_scraping)
    return {"message": "Scraping avviato in background",
            "tipo": "singolo" if search_term else "completo", "fonti": active_sources}


@router.get("/status")
async def get_scraping_status(user=Depends(get_current_user)):
    return scraping_status


@router.get("/log")
async def get_scraping_log(limit: int = 20, user=Depends(get_current_user)):
    logs = await db.scraping_log.find({}, {"_id": 0}).sort("data", -1).limit(limit).to_list(limit)
    return logs


@router.get("/categories")
async def get_scraper_categories(user=Depends(get_current_user)):
    fonti = list(SOURCES.keys()) + ["cross_reference"]
    return {"categorie": {cat: terms for cat, terms in SEARCH_TERMS.items()}, "fonti_disponibili": fonti}


@router.post("/cross-reference")
async def run_cross_reference(search_term: str, user=Depends(get_current_user)):
    results = await cross_reference_prices(db, search_term)
    return {"search_term": search_term, "risultati": len(results), "dati": results[:50]}


@router.post("/search-preview")
async def scraper_search_preview(search_term: str, fonti: Optional[List[str]] = None,
                                  user=Depends(get_current_user)):
    active_sources = fonti or list(SOURCES.keys())
    results = await scrape_product_multi(search_term, active_sources)
    by_source = {}
    for r in results:
        src = r.get("fonte", "unknown")
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(r)
    return {"search_term": search_term, "risultati_totali": len(results),
            "per_fonte": {k: len(v) for k, v in by_source.items()}, "prodotti": results[:50]}
