"""Personalized offer ranking & purchase history routes."""
import uuid
import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends
from database import db
from dependencies import get_current_user, normalize_product_name, haversine_distance, hash_password
from ranking_engine import build_user_purchase_profile, rank_offers_for_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["raccomandazioni"])


@router.get("/offerte/personalizzate")
async def get_offerte_personalizzate(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    raggio_km: float = 15,
    debug: bool = False,
    current_user: dict = Depends(get_current_user),
):
    offerte_db = await db.prodotti.find(
        {"in_offerta": True}, {"_id": 0}
    ).limit(500).to_list(500)

    if not offerte_db:
        return {"offers": [], "meta": {"isColdStart": True, "totalOffers": 0}}

    supermercati = await db.supermercati.find({}, {"_id": 0}).to_list(200)
    store_map = {s["id"]: s for s in supermercati}

    nearby_ids = None
    store_dist: dict[str, float] = {}
    if lat is not None and lng is not None:
        nearby_ids = set()
        for s in supermercati:
            d = haversine_distance(lat, lng, s["lat"], s["lng"])
            if d <= raggio_km:
                store_dist[s["id"]] = round(d, 1)
                nearby_ids.add(s["id"])

    offers = []
    for prod in offerte_db:
        sid = prod["supermercato_id"]
        if nearby_ids is not None and sid not in nearby_ids:
            continue
        store = store_map.get(sid)
        if not store:
            continue
        dist_km = store_dist.get(sid)
        if dist_km is None and lat is not None and lng is not None:
            dist_km = round(haversine_distance(lat, lng, store["lat"], store["lng"]), 1)

        offers.append({
            "offerId": prod["id"],
            "productName": prod["nome_prodotto"],
            "canonicalProductName": normalize_product_name(prod["nome_prodotto"]).lower(),
            "categoryName": prod["categoria"],
            "brand": prod.get("brand"),
            "formato": prod.get("formato", ""),
            "originalPrice": prod.get("prezzo_precedente"),
            "offerPrice": prod["prezzo"],
            "discountPercent": prod.get("sconto_percentuale"),
            "supermarketId": sid,
            "supermarketName": store.get("nome", sid),
            "userDistanceKm": dist_km,
            "inStock": True,
        })

    history = await db.storico_acquisti.find(
        {"userId": current_user["id"]}, {"_id": 0}
    ).sort("purchasedAt", -1).limit(500).to_list(500)

    profile = build_user_purchase_profile(history)
    ranked, meta = rank_offers_for_user(offers, profile, history)

    result = []
    for o in ranked:
        item = {
            "offerId": o["offerId"],
            "productName": o["productName"],
            "brand": o.get("brand"),
            "formato": o.get("formato", ""),
            "categoryName": o["categoryName"],
            "offerPrice": o["offerPrice"],
            "originalPrice": o.get("originalPrice"),
            "discountPercent": o.get("discountPercent"),
            "supermarketId": o["supermarketId"],
            "supermarketName": o["supermarketName"],
            "distanceKm": o.get("userDistanceKm"),
            "score": o.get("_score", 0),
            "reasonLabel": o.get("_reasonLabel", ""),
        }
        if debug:
            item["scoreBreakdown"] = o.get("_breakdown", {})
        result.append(item)

    if result:
        logger.info(
            "[RANKING] User %s | Cold=%s Blend=%s | Top5:",
            current_user["id"][:8], meta.get("isColdStart"), meta.get("isBlended"),
        )
        for i, r in enumerate(result[:5]):
            logger.info(
                "  #%d %s @ %s | score=%.1f | %s",
                i + 1, r["productName"], r["supermarketName"], r["score"], r["reasonLabel"],
            )

    meta["totalOffers"] = len(result)
    if profile:
        meta["profileSummary"] = {
            "topCategories": profile["topCategories"][:5],
            "topBrands": profile["topBrands"][:5],
            "totalOrders": profile["totalOrders"],
            "totalItems": profile["totalItemsPurchased"],
        }

    return {"offers": result, "meta": meta}


# ==================== PURCHASE HISTORY CRUD ====================

@router.post("/acquisti")
async def record_purchase(purchase: dict, current_user: dict = Depends(get_current_user)):
    doc = {
        "id": str(uuid.uuid4()),
        "userId": current_user["id"],
        "productId": purchase.get("productId", ""),
        "productName": purchase.get("productName", ""),
        "canonicalProductName": normalize_product_name(purchase.get("productName", "")).lower(),
        "categoryName": purchase.get("categoryName", ""),
        "brand": purchase.get("brand"),
        "quantity": purchase.get("quantity", 1),
        "unitPrice": purchase.get("unitPrice", 0),
        "purchasedAt": purchase.get("purchasedAt", datetime.now(timezone.utc).isoformat()),
        "supermarketId": purchase.get("supermarketId", ""),
        "supermarketName": purchase.get("supermarketName", ""),
    }
    await db.storico_acquisti.insert_one(doc)
    return {"message": "Acquisto registrato", "id": doc["id"]}


@router.post("/acquisti/bulk")
async def record_purchases_bulk(purchases: list, current_user: dict = Depends(get_current_user)):
    docs = []
    for p in purchases:
        docs.append({
            "id": str(uuid.uuid4()),
            "userId": current_user["id"],
            "productId": p.get("productId", ""),
            "productName": p.get("productName", ""),
            "canonicalProductName": normalize_product_name(p.get("productName", "")).lower(),
            "categoryName": p.get("categoryName", ""),
            "brand": p.get("brand"),
            "quantity": p.get("quantity", 1),
            "unitPrice": p.get("unitPrice", 0),
            "purchasedAt": p.get("purchasedAt", datetime.now(timezone.utc).isoformat()),
            "supermarketId": p.get("supermarketId", ""),
            "supermarketName": p.get("supermarketName", ""),
        })
    if docs:
        await db.storico_acquisti.insert_many(docs)
    return {"message": f"{len(docs)} acquisti registrati"}


@router.get("/acquisti")
async def get_purchase_history(limit: int = 100, current_user: dict = Depends(get_current_user)):
    items = await db.storico_acquisti.find(
        {"userId": current_user["id"]}, {"_id": 0}
    ).sort("purchasedAt", -1).limit(min(limit, 500)).to_list(min(limit, 500))
    return {"purchases": items, "total": len(items)}


# ==================== MOCK DATA SEEDER ====================

@router.post("/acquisti/seed-mock")
async def seed_mock_purchases():
    products = await db.prodotti.find({}, {"_id": 0}).limit(2000).to_list(2000)
    stores = await db.supermercati.find({}, {"_id": 0}).to_list(200)
    store_map = {s["id"]: s for s in stores}

    if not products:
        return {"error": "Nessun prodotto nel DB. Esegui prima /api/seed"}

    by_cat: dict[str, list] = {}
    for p in products:
        by_cat.setdefault(p["categoria"], []).append(p)

    test_users = [
        {"email": "heavy_buyer@test.com", "nome": "Marco Rossi", "profile": "heavy"},
        {"email": "discount_hunter@test.com", "nome": "Giulia Bianchi", "profile": "discount"},
        {"email": "new_user@test.com", "nome": "Luigi Verdi", "profile": "new"},
    ]

    results = {}
    for tu in test_users:
        existing = await db.utenti.find_one({"email": tu["email"]}, {"_id": 0})
        if not existing:
            user_id = str(uuid.uuid4())
            await db.utenti.insert_one({
                "id": user_id, "email": tu["email"], "nome": tu["nome"],
                "password_hash": hash_password("test1234"),
                "data_registrazione": datetime.now(timezone.utc).isoformat(),
                "preferenze": {
                    "raggio_max_km": 5, "max_supermercati": 3,
                    "peso_prezzo": 0.7, "peso_tempo": 0.3,
                    "supermercati_preferiti": [],
                    "notifiche_offerte": True, "notifiche_condivisione": True,
                },
                "statistiche": {"spese_totali": 0, "risparmio_totale_euro": 0, "tempo_totale_risparmiato_min": 0},
                "famiglia_id": None,
                "referral_code": f"TEST{random.randint(1000, 9999)}",
                "punti_referral": 0,
                "invitato_da": None,
            })
        else:
            user_id = existing["id"]

        await db.storico_acquisti.delete_many({"userId": user_id})

        if tu["profile"] == "new":
            results[tu["email"]] = {"userId": user_id, "purchases": 0, "note": "Cold start"}
            continue

        now = datetime.now(timezone.utc)
        if tu["profile"] == "heavy":
            target_cats = ["Latticini", "Pane e Cereali", "Igiene e Casa", "Condimenti e Salse", "Frutta e Verdura"]
            preferred_stores = ["esselunga-pioltello", "coop-pioltello", "conad-pioltello"]
            n = 45
        else:
            target_cats = ["Pane e Cereali", "Bevande", "Snack e Dolci", "Surgelati", "Latticini"]
            preferred_stores = ["lidl-pioltello", "eurospin-pioltello", "md-segrate", "penny-pioltello"]
            n = 35

        purchases = []
        for _ in range(n):
            cat = random.choice(target_cats) if random.random() < 0.75 else random.choice(list(by_cat.keys()))
            if cat not in by_cat:
                continue
            prod = random.choice(by_cat[cat])
            sid = random.choice(preferred_stores) if random.random() < 0.7 else prod["supermercato_id"]
            store = store_map.get(sid, {})
            pa = (now - timedelta(days=random.randint(1, 120))).isoformat()
            purchases.append({
                "id": str(uuid.uuid4()), "userId": user_id,
                "productId": prod["id"], "productName": prod["nome_prodotto"],
                "canonicalProductName": normalize_product_name(prod["nome_prodotto"]).lower(),
                "categoryName": prod["categoria"], "brand": prod.get("brand"),
                "quantity": random.choice([1, 1, 1, 2, 2, 3]),
                "unitPrice": prod["prezzo"], "purchasedAt": pa,
                "supermarketId": sid, "supermarketName": store.get("nome", sid),
            })

        if purchases:
            await db.storico_acquisti.insert_many(purchases)

        results[tu["email"]] = {"userId": user_id, "purchases": len(purchases), "profile": tu["profile"]}

    await db.storico_acquisti.create_index([("userId", 1), ("purchasedAt", -1)])

    return {
        "message": "Mock purchase data seeded",
        "users": results,
        "credentials": {
            "heavy_buyer": {"email": "heavy_buyer@test.com", "password": "test1234"},
            "discount_hunter": {"email": "discount_hunter@test.com", "password": "test1234"},
            "new_user": {"email": "new_user@test.com", "password": "test1234"},
        },
    }
