"""Generate base product catalog for discovered stores and import real scraped offers."""
import re
import uuid
import random
import logging
from datetime import datetime, timezone
from scraper import _map_chain, SEARCH_TERMS

logger = logging.getLogger(__name__)

BASE_CATALOG = {
    "Latticini": [
        ("Latte Intero 1L", "Granarolo", "1L", 1.49), ("Latte Parzialmente Scremato 1L", "Parmalat", "1L", 1.39),
        ("Yogurt Bianco", "Muller", "125g", 0.89), ("Yogurt Greco", "Fage", "150g", 1.29),
        ("Mozzarella", "Galbani", "125g", 1.29), ("Parmigiano Reggiano", "Parmareggio", "200g", 4.99),
        ("Burro", "Lurpak", "250g", 2.49), ("Ricotta", "Santa Lucia", "250g", 1.79),
        ("Philadelphia", "Kraft", "150g", 1.99), ("Panna da Cucina", "Parmalat", "200ml", 1.09),
    ],
    "Pane e Cereali": [
        ("Pasta Spaghetti", "Barilla", "500g", 0.99), ("Pasta Penne", "De Cecco", "500g", 1.29),
        ("Pasta Fusilli", "Barilla", "500g", 0.99), ("Riso Arborio", "Scotti", "1kg", 2.19),
        ("Farina 00", "Caputo", "1kg", 0.89), ("Pane in Cassetta", "Mulino Bianco", "400g", 1.89),
        ("Fette Biscottate", "Mulino Bianco", "315g", 1.99), ("Cornflakes", "Kellogg's", "375g", 2.79),
        ("Crackers", "Pavesi", "500g", 1.79), ("Riso Basmati", "Scotti", "500g", 1.99),
    ],
    "Frutta e Verdura": [
        ("Mele Golden", "Italia", "1kg", 1.99), ("Banane", "Chiquita", "1kg", 1.49),
        ("Arance", "Sicilia", "1kg", 1.79), ("Pomodori", "Italia", "1kg", 2.29),
        ("Insalata Iceberg", "Italia", "1pz", 0.99), ("Carote", "Italia", "1kg", 1.29),
        ("Patate", "Italia", "2kg", 2.49), ("Zucchine", "Italia", "1kg", 2.29),
        ("Limoni", "Sicilia", "500g", 1.29), ("Spinaci", "Italia", "400g", 1.99),
    ],
    "Carne e Pesce": [
        ("Petto di Pollo", "AIA", "500g", 6.99), ("Macinato Bovino", "Inalca", "400g", 5.49),
        ("Prosciutto Cotto", "Rovagnati", "100g", 2.49), ("Prosciutto Crudo", "San Daniele", "80g", 3.99),
        ("Tonno in Scatola", "Rio Mare", "160g", 2.79), ("Salmone Affumicato", "Fjord", "100g", 3.99),
        ("Bresaola", "Rigamonti", "80g", 3.99), ("Wurstel", "Wudy", "250g", 1.99),
    ],
    "Bevande": [
        ("Acqua Naturale 6x1.5L", "Sant'Anna", "9L", 2.49), ("Acqua Frizzante 6x1.5L", "San Pellegrino", "9L", 2.99),
        ("Coca Cola", "Coca-Cola", "1.5L", 1.69), ("Succo Arancia", "Santal", "1L", 1.49),
        ("Birra Lager", "Peroni", "66cl", 1.29), ("Caffe Macinato", "Lavazza", "250g", 3.99),
        ("Te Verde", "Twinings", "25pz", 2.79), ("Fanta", "Coca-Cola", "1.5L", 1.59),
    ],
    "Snack e Dolci": [
        ("Biscotti Gocciole", "Pavesi", "500g", 2.49), ("Nutella", "Ferrero", "400g", 3.49),
        ("Cioccolato Fondente", "Lindt", "100g", 2.99), ("Patatine", "San Carlo", "150g", 1.99),
        ("Gelato Vaniglia", "Algida", "500ml", 3.49), ("Marmellata Fragole", "Zuegg", "320g", 2.19),
    ],
    "Condimenti e Salse": [
        ("Olio Extravergine", "Monini", "1L", 7.99), ("Passata di Pomodoro", "Mutti", "700g", 1.49),
        ("Pesto Genovese", "Barilla", "190g", 2.49), ("Aceto Balsamico", "Ponti", "250ml", 2.99),
        ("Sale Fino", "Sale Marino", "1kg", 0.49), ("Maionese", "Calve", "225ml", 1.99),
    ],
    "Surgelati": [
        ("Pizza Margherita", "Buitoni", "350g", 2.99), ("Minestrone", "Findus", "750g", 2.99),
        ("Patate Fritte", "McCain", "750g", 2.49), ("Verdure Miste", "Orogel", "450g", 1.99),
    ],
    "Igiene e Casa": [
        ("Carta Igienica 8 rotoli", "Scottex", "8pz", 4.99), ("Detersivo Piatti", "Fairy", "650ml", 2.29),
        ("Detersivo Lavatrice", "Dash", "25 lavaggi", 7.99), ("Carta da Cucina", "Scottex", "2pz", 2.49),
    ],
    "Igiene Personale": [
        ("Shampoo", "Pantene", "250ml", 3.49), ("Bagnoschiuma", "Dove", "500ml", 2.99),
        ("Dentifricio", "Colgate", "75ml", 1.99), ("Deodorante Spray", "Dove", "150ml", 2.99),
    ],
}

CHAIN_PRICE_FACTOR = {
    "Lidl": 0.85, "Eurospin": 0.80, "MD": 0.78, "Penny": 0.82, "Aldi": 0.83,
    "iN's": 0.80, "DPiu": 0.79, "Todis": 0.81, "Prix": 0.82,
    "Coop": 1.0, "Ipercoop": 1.02, "Conad": 0.98, "Esselunga": 1.05,
    "Carrefour": 0.96, "Pam": 0.97, "Bennet": 0.99, "Famila": 0.97,
    "Il Gigante": 0.96, "Iper": 1.03, "Iperal": 1.02,
    "Despar": 1.01, "Unes": 0.97, "Sigma": 0.99, "Crai": 1.01,
    "Simply": 0.95, "NaturaSi": 1.20, "Tigros": 0.98, "A&O": 0.95,
}


async def generate_base_catalog(db, stores: list) -> int:
    """Generate base product catalog for newly discovered stores."""
    existing_store_ids = set()
    existing = await db.prodotti.distinct("supermercato_id")
    existing_store_ids = set(existing)

    new_stores = [s for s in stores if s["id"] not in existing_store_ids]
    if not new_stores:
        return 0

    products = []
    now = datetime.now(timezone.utc).isoformat()

    for store in new_stores:
        factor = CHAIN_PRICE_FACTOR.get(store["catena"], 1.0)
        for categoria, items in BASE_CATALOG.items():
            for nome, brand, formato, prezzo_base in items:
                prezzo = round(prezzo_base * factor * random.uniform(0.96, 1.04), 2)
                in_offerta = random.random() < 0.10
                sconto = None
                prezzo_prec = None
                if in_offerta:
                    sconto = random.choice([10, 15, 20, 25, 30])
                    prezzo_prec = prezzo
                    prezzo = round(prezzo * (1 - sconto / 100), 2)

                prod_slug = re.sub(r'[^a-z0-9]+', '-', nome.lower())[:40]
                products.append({
                    "id": f"{prod_slug}-{store['id']}",
                    "nome_prodotto": nome,
                    "categoria": categoria,
                    "brand": brand,
                    "formato": formato,
                    "supermercato_id": store["id"],
                    "prezzo": prezzo,
                    "prezzo_precedente": prezzo_prec,
                    "in_offerta": in_offerta,
                    "sconto_percentuale": sconto,
                    "data_aggiornamento": now,
                    "fonte_prezzo": "catalogo_base",
                })

    if products:
        await db.prodotti.insert_many(products)
        logger.info(f"[Catalog] Created {len(products)} products for {len(new_stores)} new stores")

    return len(products)


async def import_scraped_offers(db, scraped_data: list, stores: list) -> dict:
    """Import real scraped offers and map them to discovered stores by chain."""
    from pymongo import UpdateOne

    chain_to_stores: dict[str, list] = {}
    for s in stores:
        chain_lower = s["catena"].lower()
        chain_to_stores.setdefault(chain_lower, []).append(s)

    created = 0
    updated = 0
    operations = []
    now = datetime.now(timezone.utc).isoformat()

    for item in scraped_data:
        raw_chain = _map_chain(item.get("catena", "") or item.get("negozio_originale", ""))
        matching = chain_to_stores.get(raw_chain.lower(), [])
        if not matching:
            for ck, sv in chain_to_stores.items():
                if raw_chain.lower() in ck or ck in raw_chain.lower():
                    matching = sv
                    break

        if not matching:
            continue

        nome = item["nome_prodotto"]
        prod_slug = re.sub(r'[^a-z0-9]+', '-', nome.lower())[:40]

        for store in matching:
            prod_id = f"dc-{prod_slug}-{store['id']}"
            doc = {
                "id": prod_id,
                "nome_prodotto": nome,
                "categoria": item.get("search_term", "Altro"),
                "brand": "",
                "formato": "",
                "supermercato_id": store["id"],
                "prezzo": item["prezzo"],
                "prezzo_precedente": item.get("prezzo_precedente"),
                "in_offerta": item.get("in_offerta", False),
                "sconto_percentuale": item.get("sconto_percentuale"),
                "data_aggiornamento": now,
                "fonte_prezzo": "doveconviene",
            }
            operations.append(UpdateOne({"id": prod_id}, {"$set": doc}, upsert=True))

    if operations:
        result = await db.prodotti.bulk_write(operations)
        created = result.upserted_count
        updated = result.modified_count
        logger.info(f"[Import] Created {created}, updated {updated} from scraping")

    return {"created": created, "updated": updated, "total_ops": len(operations)}
