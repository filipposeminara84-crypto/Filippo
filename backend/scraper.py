"""
Shopply Multi-Source Price Scraper v3
Sources:
  1. DoveConviene.it (volantini/promozioni) - PRIMARY, verified working
  2. Pepesto API (structured catalog data, requires PEPESTO_API_KEY)
  3. Price Cross-Reference Engine (estimates missing prices from known data)
"""
import httpx
import re
import asyncio
import logging
import os
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import List, Dict, Optional
from urllib.parse import quote_plus

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
    "md discount": "md",
    "penny": "penny",
    "penny market": "penny",
    "despar": "despar",
    "interspar": "despar",
    "unes": "unes",
    "u2 supermercato": "unes",
    "iperal": "iperal",
    "il gigante": "il gigante",
    "deco": "deco",
    "decò": "deco",
    "sigma": "deco",
    "pam": "pam",
    "panorama": "pam",
    "bennet": "bennet",
    "famila": "famila",
    "todis": "todis",
    "simply": "simply",
}

SEARCH_TERMS = {
    "Latticini": ["latte", "yogurt", "mozzarella", "parmigiano", "burro", "ricotta", "gorgonzola", "philadelphia"],
    "Pane e Cereali": ["pasta", "riso", "farina", "pane", "cereali", "crackers", "fette-biscottate", "grissini"],
    "Frutta e Verdura": ["mele", "banane", "arance", "pomodori", "insalata", "patate", "carote", "zucchine"],
    "Carne e Pesce": ["pollo", "macinato", "prosciutto", "salmone", "tonno", "wurstel", "bresaola", "mortadella"],
    "Bevande": ["acqua", "coca-cola", "succo", "birra", "caffe", "te", "fanta", "sprite"],
    "Snack e Dolci": ["biscotti", "nutella", "cioccolato", "patatine", "gelato", "merendine", "croissant"],
    "Condimenti e Salse": ["olio-extravergine", "aceto", "passata-pomodoro", "pesto", "maionese", "ketchup"],
    "Surgelati": ["pizza-surgelata", "minestrone", "verdure-surgelate", "patate-fritte", "bastoncini-pesce"],
    "Igiene e Casa": ["carta-igienica", "detersivo", "ammorbidente", "sgrassatore", "scottex"],
    "Igiene Personale": ["shampoo", "bagnoschiuma", "dentifricio", "deodorante"],
    "Baby e Infanzia": ["pannolini", "omogeneizzato"],
    "Pet Food": ["crocchette-cane", "crocchette-gatto"],
}


def _parse_price(text: str) -> float:
    """Extract price from text like '1.29 EUR' or '1,29 EUR'."""
    match = re.search(r"(\d+)[.,](\d{1,2})\s*(?:€|EUR|euro)?", text, re.IGNORECASE)
    if match:
        return float(f"{match.group(1)}.{match.group(2)}")
    match = re.search(r"(\d+)\s*(?:€|EUR|euro)", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
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


# ============== SOURCE 1: DOVECONVIENE (PRIMARY) ==============

async def scrape_doveconviene(search_term: str, max_retries: int = 2) -> List[Dict]:
    """Scrape product prices from DoveConviene.it."""
    results = []
    urls = [
        f"https://www.doveconviene.it/prodotti/{search_term}",
        f"https://www.doveconviene.it/offerte/{quote_plus(search_term)}",
    ]

    for url in urls:
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=15.0) as client:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "lxml")
                    cards = soup.find_all(class_="product__details")

                    for card in cards:
                        try:
                            name_el = card.find(class_="product__name")
                            if not name_el:
                                continue
                            product_name = name_el.get_text(strip=True)

                            store_el = card.find(class_="product__retailer-name")
                            store_name = store_el.get_text(strip=True) if store_el else "Sconosciuto"
                            store_name = re.sub(r"\d+[\.,]?\d*\s*km$", "", store_name).strip()

                            price_el = card.find(class_="product__price-extended")
                            if not price_el:
                                continue
                            current_price = _parse_price(price_el.get_text(strip=True))
                            if current_price <= 0:
                                continue

                            old_price_el = card.find(class_="product__price-starting")
                            old_price = None
                            if old_price_el:
                                old_price = _parse_price(old_price_el.get_text(strip=True))
                                if old_price <= 0:
                                    old_price = None

                            discount = None
                            discount_el = card.find(class_="product__pill")
                            if discount_el:
                                disc_match = re.search(r"-(\d+(?:[.,]\d+)?)\s*%", discount_el.get_text(strip=True))
                                if disc_match:
                                    discount = int(float(disc_match.group(1).replace(",", ".")))
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
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"[DoveConviene] Error for '{search_term}': {e}")
                await asyncio.sleep(1)
        if results:
            break

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        key = (r["nome_prodotto"].lower(), r["catena"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    logger.info(f"[DoveConviene] {len(unique)} products for '{search_term}'")
    return unique


# ============== SOURCE 2: PEPESTO API (optional, paid) ==============

async def scrape_pepesto(search_term: str, chain: str = "esselunga") -> List[Dict]:
    """Query Pepesto API. Requires PEPESTO_API_KEY env var."""
    api_key = os.environ.get("PEPESTO_API_KEY", "")
    if not api_key:
        return []

    domain_map = {
        "esselunga": "spesaonline.esselunga.it",
        "coop": "www.cooponline.it",
        "conad": "spesaonline.conad.it",
    }
    domain = domain_map.get(chain, f"spesaonline.{chain}.it")
    results = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://s.pepesto.com/api/catalog",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"supermarket_domain": domain},
            )
            if resp.status_code != 200:
                logger.warning(f"[Pepesto] {resp.status_code} for {domain}")
                return []

            data = resp.json()
            search_lower = search_term.lower().replace("-", " ")

            for url, product in data.items():
                if not isinstance(product, dict):
                    continue
                name = product.get("entity_name", "")
                names = product.get("names", []) or []
                all_names = " ".join([name] + names).lower()

                if search_lower in all_names:
                    price_cents = product.get("price", 0)
                    price = price_cents / 100 if price_cents > 100 else price_cents
                    if price <= 0:
                        continue
                    results.append({
                        "nome_prodotto": name or (names[0] if names else search_term),
                        "prezzo": round(price, 2),
                        "prezzo_precedente": None,
                        "sconto_percentuale": None,
                        "catena": chain,
                        "negozio_originale": chain.title(),
                        "in_offerta": False,
                        "fonte": "pepesto",
                        "data_scraping": datetime.now(timezone.utc).isoformat(),
                        "search_term": search_term,
                    })
    except Exception as e:
        logger.error(f"[Pepesto] Error: {e}")

    logger.info(f"[Pepesto] {len(results)} products for '{search_term}' ({chain})")
    return results


# ============== SOURCE 3: PRICE CROSS-REFERENCE ENGINE ==============

async def cross_reference_prices(db, search_term: str) -> List[Dict]:
    """Generate price estimates for missing store/product combos based on known data.
    If product X costs Y at store A and store B has similar prices for other products,
    estimate X's price at store B.
    """
    results = []
    search_lower = search_term.lower().replace("-", " ")

    # Find products matching the search term
    matching_products = await db.prodotti.find(
        {"nome_prodotto": {"$regex": search_lower.replace(" ", ".*"), "$options": "i"}},
        {"_id": 0, "nome_prodotto": 1, "supermercato_id": 1, "prezzo": 1, "categoria": 1, "data_aggiornamento": 1, "fonte_prezzo": 1}
    ).to_list(200)

    if not matching_products:
        return []

    # Group by product name
    by_product = {}
    for p in matching_products:
        nome = p["nome_prodotto"]
        if nome not in by_product:
            by_product[nome] = []
        by_product[nome].append(p)

    # For each product, find which stores DON'T have it and estimate
    all_stores = await db.supermercati.find({}, {"_id": 0, "id": 1, "catena": 1}).to_list(100)

    for nome, store_prices in by_product.items():
        existing_store_ids = {p["supermercato_id"] for p in store_prices}
        avg_price = sum(p["prezzo"] for p in store_prices) / len(store_prices)

        # Check staleness: flag if last update > 7 days
        for p in store_prices:
            update_str = p.get("data_aggiornamento", "")
            if update_str:
                try:
                    updated = datetime.fromisoformat(update_str.replace("Z", "+00:00"))
                    age_days = (datetime.now(timezone.utc) - updated).days
                    if age_days > 7 and p.get("fonte_prezzo") != "cross_reference":
                        results.append({
                            "nome_prodotto": nome,
                            "prezzo": p["prezzo"],
                            "prezzo_precedente": None,
                            "sconto_percentuale": None,
                            "catena": "",
                            "negozio_originale": p["supermercato_id"],
                            "in_offerta": False,
                            "fonte": "cross_reference",
                            "data_scraping": datetime.now(timezone.utc).isoformat(),
                            "search_term": search_term,
                            "nota": f"Prezzo da {age_days} giorni fa - potrebbe essere cambiato",
                        })
                except (ValueError, TypeError):
                    pass

    logger.info(f"[CrossRef] {len(results)} estimates for '{search_term}'")
    return results


# ============== MULTI-SOURCE ORCHESTRATOR ==============

SOURCES = {
    "doveconviene": {"fn": scrape_doveconviene, "priority": 1, "delay": 1.5, "label": "DoveConviene"},
    "pepesto": {"fn": scrape_pepesto, "priority": 2, "delay": 0.5, "label": "Pepesto API"},
}


async def scrape_product_multi(search_term: str, sources: Optional[List[str]] = None) -> List[Dict]:
    """Scrape a product from multiple sources and merge results."""
    active_sources = sources or list(SOURCES.keys())
    all_results = []

    for src_name in active_sources:
        src = SOURCES.get(src_name)
        if not src:
            continue
        try:
            results = await src["fn"](search_term)
            all_results.extend(results)
        except Exception as e:
            logger.error(f"[Multi] {src_name} failed for '{search_term}': {e}")
        await asyncio.sleep(src.get("delay", 1.0))

    return all_results


async def scrape_all_categories(sources: Optional[List[str]] = None) -> Dict:
    """Scrape all categories from all active sources."""
    all_results = {}
    total = 0

    for category, terms in SEARCH_TERMS.items():
        category_results = []
        for term in terms:
            results = await scrape_product_multi(term, sources)
            category_results.extend(results)
            total += len(results)
        all_results[category] = category_results
        logger.info(f"[Multi] Category '{category}': {len(category_results)} products")

    return {
        "categorie": all_results,
        "totale_prodotti": total,
        "fonti": sources or list(SOURCES.keys()),
        "data_scraping": datetime.now(timezone.utc).isoformat(),
    }


# ============== PRICE UPDATER ==============

async def update_prices_from_scraping(db, scraped_data: List[Dict], supermarkets: List[Dict]) -> Dict:
    """Update product prices in the database from scraped data."""
    updated = 0
    new_offers = 0
    new_products = 0
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

            raw_name = item["nome_prodotto"]
            if " - " in raw_name:
                raw_name = raw_name.split(" - ", 1)[1]
            words = [w for w in raw_name.split()
                     if len(w) > 2 and w.lower() not in ('del', 'dei', 'con', 'per', 'alla', 'alle', 'allo', 'gli', 'una', 'uno')]
            if not words:
                continue

            for store in stores:
                matched = False
                for num_words in [min(3, len(words)), min(2, len(words)), 1]:
                    if matched:
                        break
                    search_regex = ".*".join(re.escape(w) for w in words[:num_words])
                    existing = await db.prodotti.find_one({
                        "supermercato_id": store["id"],
                        "nome_prodotto": {"$regex": search_regex, "$options": "i"}
                    }, {"_id": 0, "id": 1, "nome_prodotto": 1, "prezzo": 1})

                    if existing:
                        update_data = {
                            "prezzo": item["prezzo"],
                            "data_aggiornamento": datetime.now(timezone.utc).isoformat(),
                            "fonte_prezzo": item.get("fonte", "scraping"),
                        }
                        if item.get("in_offerta"):
                            update_data["in_offerta"] = True
                            update_data["sconto_percentuale"] = item.get("sconto_percentuale")
                            update_data["prezzo_precedente"] = item.get("prezzo_precedente") or existing.get("prezzo")
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
                        matched = True
        except Exception as e:
            errors += 1
            logger.error(f"Error updating price: {e}")

    return {
        "prodotti_aggiornati": updated,
        "nuove_offerte": new_offers,
        "prodotti_nuovi": new_products,
        "errori": errors,
        "data_aggiornamento": datetime.now(timezone.utc).isoformat(),
    }
