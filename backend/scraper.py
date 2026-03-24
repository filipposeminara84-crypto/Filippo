"""
Shopply Price Scraper - Scrapes prices from DoveConviene.it
"""
import httpx
import re
import asyncio
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import List, Dict

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}

CHAIN_MAP = {
    "esselunga": "esselunga",
    "coop": "coop",
    "ipercoop": "coop",
    "conad": "conad",
    "conad city": "conad",
    "conad superstore": "conad",
    "spazio conad": "conad",
    "carrefour": "carrefour",
    "carrefour market": "carrefour",
    "carrefour express": "carrefour",
    "carrefour ipermercati": "carrefour",
    "lidl": "lidl",
    "eurospin": "eurospin",
    "aldi": "aldi",
    "md": "md",
    "penny": "penny",
    "despar": "despar",
    "interspar": "despar",
    "unes": "unes",
    "u2 supermercato": "unes",
    "iperal": "iperal",
    "il gigante": "il gigante",
    "deco": "deco",
    "decò": "deco",
    "sigma": "deco",
}

SEARCH_TERMS = {
    "Latticini": ["latte", "yogurt", "mozzarella", "parmigiano", "burro", "ricotta", "gorgonzola"],
    "Pane e Cereali": ["pasta", "riso", "farina", "pane", "cereali", "crackers", "fette-biscottate"],
    "Frutta e Verdura": ["mele", "banane", "arance", "pomodori", "insalata", "patate", "carote"],
    "Carne e Pesce": ["pollo", "macinato", "prosciutto", "salmone", "tonno", "wurstel"],
    "Bevande": ["acqua", "coca-cola", "succo", "birra", "caffe", "te"],
    "Snack e Dolci": ["biscotti", "nutella", "cioccolato", "patatine", "gelato", "merendine"],
    "Condimenti e Salse": ["olio-extravergine", "aceto", "passata-pomodoro", "pesto", "maionese"],
    "Surgelati": ["pizza-surgelata", "minestrone", "verdure-surgelate", "patate-fritte"],
    "Igiene e Casa": ["carta-igienica", "detersivo", "ammorbidente", "sgrassatore"],
    "Igiene Personale": ["shampoo", "bagnoschiuma", "dentifricio", "deodorante"],
    "Baby e Infanzia": ["pannolini", "omogeneizzato"],
    "Pet Food": ["crocchette-cane", "crocchette-gatto"],
}


def _parse_price(text: str) -> float:
    """Extract price from text like '1.29€' or '1,29€'"""
    match = re.search(r"(\d+)[.,](\d{2})\s*€", text)
    if match:
        return float(f"{match.group(1)}.{match.group(2)}")
    return 0.0


def _map_chain(store_name: str) -> str:
    """Map a store name to our chain identifier."""
    lower = store_name.lower().strip()
    if lower in CHAIN_MAP:
        return CHAIN_MAP[lower]
    for key, val in CHAIN_MAP.items():
        if key in lower or lower in key:
            return val
    return lower


async def scrape_doveconviene(search_term: str, max_retries: int = 2) -> List[Dict]:
    """Scrape product prices from DoveConviene.it for a given search term."""
    url = f"https://www.doveconviene.it/prodotti/{search_term}"
    results = []

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"DoveConviene returned {resp.status_code} for '{search_term}'")
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                cards = soup.find_all(class_="product__details")

                for card in cards:
                    try:
                        # Product name
                        name_el = card.find(class_="product__name")
                        if not name_el:
                            continue
                        product_name = name_el.get_text(strip=True)

                        # Store name
                        store_el = card.find(class_="product__retailer-name")
                        store_name = store_el.get_text(strip=True) if store_el else "Sconosciuto"
                        # Remove distance info that might be appended
                        store_name = re.sub(r"\d+[\.,]?\d*\s*km$", "", store_name).strip()

                        # Current price
                        price_el = card.find(class_="product__price-extended")
                        if not price_el:
                            continue
                        current_price = _parse_price(price_el.get_text(strip=True))
                        if current_price <= 0:
                            continue

                        # Old price
                        old_price_el = card.find(class_="product__price-starting")
                        old_price = None
                        if old_price_el:
                            old_price = _parse_price(old_price_el.get_text(strip=True))
                            if old_price <= 0:
                                old_price = None

                        # Discount
                        discount = None
                        discount_el = card.find(class_="product__pill")
                        if discount_el:
                            disc_match = re.search(r"-(\d+(?:[.,]\d+)?)\s*%", discount_el.get_text(strip=True))
                            if disc_match:
                                discount = int(float(disc_match.group(1).replace(",", ".")))
                        # Calculate discount from prices if not found
                        if discount is None and old_price and old_price > current_price:
                            discount = round((1 - current_price / old_price) * 100)

                        chain = _map_chain(store_name)

                        results.append({
                            "nome_prodotto": product_name,
                            "prezzo": current_price,
                            "prezzo_precedente": old_price,
                            "sconto_percentuale": discount,
                            "catena": chain,
                            "negozio_originale": store_name,
                            "in_offerta": discount is not None and discount > 0,
                            "fonte": "doveconviene",
                            "data_scraping": datetime.now(timezone.utc).isoformat(),
                            "search_term": search_term,
                        })
                    except Exception:
                        continue

                if results:
                    break

        except httpx.TimeoutException:
            logger.warning(f"Timeout scraping DoveConviene for '{search_term}' (attempt {attempt+1})")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Error scraping DoveConviene for '{search_term}': {e}")
            await asyncio.sleep(1)

    logger.info(f"Scraped {len(results)} products for '{search_term}'")
    return results


async def scrape_all_categories() -> Dict:
    """Scrape all categories and return structured results."""
    all_results = {}
    total = 0
    for category, terms in SEARCH_TERMS.items():
        category_results = []
        for term in terms:
            results = await scrape_doveconviene(term)
            category_results.extend(results)
            total += len(results)
            await asyncio.sleep(1.5)
        all_results[category] = category_results
        logger.info(f"Scraped {len(category_results)} products for category '{category}'")

    return {
        "categorie": all_results,
        "totale_prodotti": total,
        "data_scraping": datetime.now(timezone.utc).isoformat(),
    }


async def update_prices_from_scraping(db, scraped_data: List[Dict], supermarkets: List[Dict]) -> Dict:
    """Update product prices in the database from scraped data."""
    updated = 0
    new_offers = 0
    errors = 0

    chain_to_stores = {}
    for sup in supermarkets:
        chain = sup["catena"].lower()
        if chain not in chain_to_stores:
            chain_to_stores[chain] = []
        chain_to_stores[chain].append(sup)

    for item in scraped_data:
        try:
            chain = item.get("catena", "").lower()
            stores = chain_to_stores.get(chain, [])
            if not stores:
                continue

            # Extract first meaningful word from product name for matching
            raw_name = item["nome_prodotto"]
            # Remove brand prefix "Brand - Product"
            if " - " in raw_name:
                raw_name = raw_name.split(" - ", 1)[1]
            # Take first two words for matching
            words = [w for w in raw_name.split() if len(w) > 2]
            if not words:
                continue
            search_regex = words[0]

            for store in stores:
                existing = await db.prodotti.find_one({
                    "supermercato_id": store["id"],
                    "nome_prodotto": {"$regex": search_regex, "$options": "i"}
                }, {"_id": 0})

                if existing:
                    update_data = {
                        "prezzo": item["prezzo"],
                        "data_aggiornamento": datetime.now(timezone.utc).isoformat(),
                        "fonte_prezzo": "doveconviene",
                    }
                    if item["in_offerta"]:
                        update_data["in_offerta"] = True
                        update_data["sconto_percentuale"] = item["sconto_percentuale"]
                        update_data["prezzo_precedente"] = item["prezzo_precedente"]
                        new_offers += 1
                    else:
                        update_data["in_offerta"] = False
                        update_data["sconto_percentuale"] = None
                        update_data["prezzo_precedente"] = None

                    await db.prodotti.update_one(
                        {"id": existing["id"]},
                        {"$set": update_data}
                    )
                    updated += 1
        except Exception as e:
            errors += 1
            logger.error(f"Error updating price: {e}")

    return {
        "prodotti_aggiornati": updated,
        "nuove_offerte": new_offers,
        "errori": errors,
        "data_aggiornamento": datetime.now(timezone.utc).isoformat(),
    }
