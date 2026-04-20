"""Shopply - Personalized Offer Ranking Engine.

Modules:
  1. build_user_purchase_profile(history)
  2. score_offer_for_user(offer, profile, history)
  3. rank_offers_for_user(offers, profile, history)
  4. apply_cold_start_fallback(offers)
  5. diversify_ranked_offers(ranked)
  6. get_offer_reason_label(breakdown)
"""
import math
from datetime import datetime, timezone
from collections import defaultdict

# ==================== CONFIGURATION ====================

WEIGHTS = {
    "category": 0.30,
    "brand": 0.20,
    "product": 0.15,
    "recency": 0.15,
    "price_fit": 0.10,
    "distance": 0.05,
    "discount": 0.05,
}

BONUS_COMPLEMENTARY = 5
BONUS_REPEAT_PURCHASE = 8
PENALTY_OUTLIER_PRICE = -5
DECAY_HALF_LIFE_DAYS = 45

COMPLEMENTARY_MAP = {
    "Pane e Cereali": ["Condimenti e Salse", "Latticini", "Snack e Dolci"],
    "Latticini": ["Pane e Cereali", "Snack e Dolci", "Bevande"],
    "Frutta e Verdura": ["Latticini", "Condimenti e Salse", "Carne e Pesce"],
    "Carne e Pesce": ["Condimenti e Salse", "Frutta e Verdura", "Pane e Cereali"],
    "Bevande": ["Snack e Dolci", "Surgelati"],
    "Snack e Dolci": ["Bevande", "Latticini"],
    "Condimenti e Salse": ["Pane e Cereali", "Carne e Pesce", "Frutta e Verdura"],
    "Surgelati": ["Condimenti e Salse", "Bevande"],
    "Igiene e Casa": ["Igiene Personale"],
    "Igiene Personale": ["Igiene e Casa"],
    "Baby e Infanzia": ["Latticini", "Igiene Personale"],
    "Pet Food": [],
}

RECURRING_CATEGORIES = {
    "Latticini", "Pane e Cereali", "Frutta e Verdura",
    "Bevande", "Igiene e Casa", "Baby e Infanzia",
}

RECURRING_KEYWORDS = {
    "acqua", "latte", "pane", "uova", "pasta", "riso", "farina",
    "carta", "detersivo", "sapone", "burro", "yogurt", "pannolini",
    "caffe", "zucchero", "sale", "olio",
}

ESSENTIAL_CATEGORIES = {
    "Latticini", "Pane e Cereali", "Frutta e Verdura",
    "Carne e Pesce", "Bevande", "Condimenti e Salse",
}


# ==================== HELPERS ====================

def _parse_dt(iso_str: str) -> datetime | None:
    try:
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1] + "+00:00"
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _time_decay(purchased_at: str) -> float:
    dt = _parse_dt(purchased_at)
    if dt is None:
        return 0.1
    days = (datetime.now(timezone.utc) - dt).total_seconds() / 86400
    return math.exp(-days / DECAY_HALF_LIFE_DAYS)


def _normalize_scores(raw: dict[str, float]) -> list[dict]:
    if not raw:
        return []
    mx = max(raw.values()) or 1
    return sorted(
        [{"name": k, "score": round(v / mx * 100, 1)} for k, v in raw.items()],
        key=lambda x: -x["score"],
    )


# ==================== 1. BUILD PROFILE ====================

def build_user_purchase_profile(history: list) -> dict | None:
    if not history:
        return None

    cat_raw = defaultdict(float)
    brand_raw = defaultdict(float)
    prod_raw = defaultdict(float)
    cat_prices: dict[str, list[float]] = defaultdict(list)
    all_prices: list[float] = []
    total_items = 0
    last_pa = None
    order_dates: set[str] = set()

    for item in history:
        w = _time_decay(item.get("purchasedAt", ""))
        qty = item.get("quantity", 1)

        cat = item.get("categoryName", "")
        if cat:
            cat_raw[cat] += w * qty
            p = item.get("unitPrice", 0)
            if p > 0:
                cat_prices[cat].append(p)

        brand = item.get("brand")
        if brand:
            brand_raw[brand] += w * qty

        canonical = item.get("canonicalProductName", item.get("productName", ""))
        if canonical:
            prod_raw[canonical.lower()] += w * qty

        price = item.get("unitPrice", 0)
        if price > 0:
            all_prices.append(price)
        total_items += qty

        pa = item.get("purchasedAt", "")
        if pa:
            if last_pa is None or pa > last_pa:
                last_pa = pa
            order_dates.add(pa[:10])

    avg_price = sum(all_prices) / len(all_prices) if all_prices else 0
    cat_avg = {k: sum(v) / len(v) for k, v in cat_prices.items() if v}

    return {
        "topCategories": _normalize_scores(dict(cat_raw)),
        "topBrands": _normalize_scores(dict(brand_raw)),
        "topProducts": _normalize_scores(dict(prod_raw)),
        "avgItemPrice": round(avg_price, 2),
        "categoryAvgPrices": cat_avg,
        "lastPurchaseAt": last_pa,
        "totalOrders": len(order_dates),
        "totalItemsPurchased": total_items,
    }


# ==================== INDIVIDUAL SCORES ====================

def _score_category_affinity(offer: dict, profile: dict) -> float:
    cat = offer.get("categoryName", "")
    for e in profile["topCategories"]:
        if e["name"] == cat:
            return e["score"]
    return 0


def _score_brand_affinity(offer: dict, profile: dict) -> float:
    brand = offer.get("brand")
    if not brand:
        return 30  # neutral
    for e in profile["topBrands"]:
        if e["name"] == brand:
            return e["score"]
    return 0


def _score_product_affinity(offer: dict, profile: dict) -> float:
    canonical = offer.get("canonicalProductName", offer.get("productName", "")).lower()
    for e in profile["topProducts"]:
        if e["name"] == canonical:
            return e["score"]
        if e["name"] in canonical or canonical in e["name"]:
            return e["score"] * 0.6
    return 0


def _score_recency(offer: dict, history: list) -> float:
    cat = offer.get("categoryName", "")
    canonical = offer.get("canonicalProductName", "").lower()
    now = datetime.now(timezone.utc)
    best_days = 999

    for item in history:
        if item.get("categoryName") != cat and item.get("canonicalProductName", "").lower() != canonical:
            continue
        dt = _parse_dt(item.get("purchasedAt", ""))
        if dt is None:
            continue
        days = (now - dt).total_seconds() / 86400
        if days < best_days:
            best_days = days

    if best_days <= 7:
        return 100
    if best_days <= 30:
        return 80
    if best_days <= 60:
        return 60
    if best_days <= 120:
        return 40
    return 20


def _score_price_fit(offer: dict, profile: dict) -> float:
    price = offer.get("offerPrice", 0)
    if price <= 0:
        return 50
    cat = offer.get("categoryName", "")
    avg = profile.get("categoryAvgPrices", {}).get(cat, profile.get("avgItemPrice", 0))
    if avg <= 0:
        return 50
    ratio = price / avg
    if 0.7 <= ratio <= 1.3:
        return 100
    if 0.5 <= ratio <= 1.5:
        return 70
    if 0.3 <= ratio <= 2.0:
        return 40
    return 20


def _score_distance(offer: dict) -> float:
    dist = offer.get("userDistanceKm")
    if dist is None:
        return 50
    if dist <= 1:
        return 100
    if dist <= 3:
        return 85
    if dist <= 5:
        return 70
    if dist <= 10:
        return 50
    return 20


def _score_discount(offer: dict) -> float:
    disc = offer.get("discountPercent")
    if disc and disc > 0:
        return min(100, disc * 3.33)
    orig = offer.get("originalPrice")
    current = offer.get("offerPrice", 0)
    if orig and orig > current and current > 0:
        calc = (orig - current) / orig * 100
        return min(100, calc * 3.33)
    return 15


def _complementary_bonus(offer: dict, history: list) -> float:
    cat = offer.get("categoryName", "")
    now = datetime.now(timezone.utc)
    recent_cats: set[str] = set()
    for item in history:
        dt = _parse_dt(item.get("purchasedAt", ""))
        if dt and (now - dt).days <= 30:
            recent_cats.add(item.get("categoryName", ""))
    for rc in recent_cats:
        if cat in COMPLEMENTARY_MAP.get(rc, []):
            return BONUS_COMPLEMENTARY
    return 0


def _repeat_purchase_bonus(offer: dict, profile: dict) -> float:
    cat = offer.get("categoryName", "")
    name_lower = offer.get("productName", "").lower()
    if cat in RECURRING_CATEGORIES:
        for e in profile["topCategories"]:
            if e["name"] == cat and e["score"] >= 40:
                return BONUS_REPEAT_PURCHASE
    for kw in RECURRING_KEYWORDS:
        if kw in name_lower:
            return BONUS_REPEAT_PURCHASE * 0.5
    return 0


# ==================== 2. SCORE SINGLE OFFER ====================

def score_offer_for_user(offer: dict, profile: dict, history: list) -> dict:
    cat = _score_category_affinity(offer, profile)
    brand = _score_brand_affinity(offer, profile)
    product = _score_product_affinity(offer, profile)
    recency = _score_recency(offer, history)
    price_fit = _score_price_fit(offer, profile)
    distance = _score_distance(offer)
    discount = _score_discount(offer)

    base = (
        WEIGHTS["category"] * cat
        + WEIGHTS["brand"] * brand
        + WEIGHTS["product"] * product
        + WEIGHTS["recency"] * recency
        + WEIGHTS["price_fit"] * price_fit
        + WEIGHTS["distance"] * distance
        + WEIGHTS["discount"] * discount
    )

    comp = _complementary_bonus(offer, history)
    repeat = _repeat_purchase_bonus(offer, profile)

    outlier = 0
    offer_price = offer.get("offerPrice", 0)
    cat_name = offer.get("categoryName", "")
    avg = profile.get("categoryAvgPrices", {}).get(cat_name, 0)
    if avg > 0 and offer_price > 0:
        ratio = offer_price / avg
        if ratio > 2.5 or ratio < 0.2:
            outlier = PENALTY_OUTLIER_PRICE

    final = max(0, min(100, base + comp + repeat + outlier))

    return {
        "finalScore": round(final, 1),
        "categoryAffinity": round(cat, 1),
        "brandAffinity": round(brand, 1),
        "productAffinity": round(product, 1),
        "recencyScore": round(recency, 1),
        "priceFitScore": round(price_fit, 1),
        "distanceScore": round(distance, 1),
        "discountScore": round(discount, 1),
        "complementaryBonus": round(comp, 1),
        "repeatPurchaseBonus": round(repeat, 1),
        "outlierPricePenalty": round(outlier, 1),
    }


# ==================== 6. REASON LABEL ====================

def get_offer_reason_label(breakdown: dict) -> str:
    if breakdown.get("productAffinity", 0) >= 50:
        return "Comprato spesso"
    if breakdown.get("repeatPurchaseBonus", 0) > 0:
        return "Da riordinare"
    if breakdown.get("complementaryBonus", 0) > 0:
        return "Prodotto correlato"
    if breakdown.get("categoryAffinity", 0) >= 60:
        return "In base ai tuoi acquisti"
    if breakdown.get("discountScore", 0) >= 80:
        return "Ottimo sconto"
    if breakdown.get("distanceScore", 0) >= 85:
        return "Vicino a te"
    if breakdown.get("brandAffinity", 0) >= 60:
        return "In base ai tuoi acquisti"
    return ""


# ==================== 5. DIVERSITY GUARDRAILS ====================

def diversify_ranked_offers(ranked: list) -> list:
    if len(ranked) <= 2:
        return ranked

    result = []
    remaining = list(ranked)

    while remaining:
        placed = False
        for i, offer in enumerate(remaining):
            if len(result) >= 2 and len(remaining) > 1:
                last_cats = [r.get("categoryName") for r in result[-2:]]
                last_stores = [r.get("supermarketId") for r in result[-2:]]
                if all(c == offer.get("categoryName") for c in last_cats):
                    continue
                if all(s == offer.get("supermarketId") for s in last_stores):
                    continue
            result.append(offer)
            remaining.pop(i)
            placed = True
            break
        if not placed:
            result.append(remaining.pop(0))

    return result


# ==================== 4. COLD START FALLBACK ====================

def apply_cold_start_fallback(offers: list) -> list:
    for offer in offers:
        score = 0
        dist = offer.get("userDistanceKm")
        score += 40 * _score_distance(offer) / 100 if dist is not None else 20
        score += 30 * _score_discount(offer) / 100
        if offer.get("categoryName") in ESSENTIAL_CATEGORIES:
            score += 15
        if offer.get("inStock") is not False:
            score += 5

        offer["_score"] = round(score, 1)
        offer["_breakdown"] = {
            "finalScore": round(score, 1),
            "fallback": True,
            "distanceScore": round(_score_distance(offer), 1),
            "discountScore": round(_score_discount(offer), 1),
        }
        label = ""
        if dist is not None and dist <= 5:
            label = "Vicino a te"
        elif (offer.get("discountPercent") or 0) > 15:
            label = "Ottimo sconto"
        offer["_reasonLabel"] = label

    offers.sort(key=lambda x: -x["_score"])
    return offers


# ==================== 3. RANK ALL OFFERS ====================

def rank_offers_for_user(
    offers: list,
    profile: dict | None,
    history: list,
) -> tuple[list, dict]:
    is_cold = (
        profile is None
        or profile.get("totalItemsPurchased", 0) < 10
        or profile.get("totalOrders", 0) < 3
    )
    has_some = profile is not None and profile.get("totalItemsPurchased", 0) > 0
    meta = {"isColdStart": is_cold, "isBlended": False}

    if is_cold and not has_some:
        return apply_cold_start_fallback(offers), meta

    if is_cold and has_some:
        meta["isBlended"] = True
        for offer in offers:
            bd = score_offer_for_user(offer, profile, history)
            fb = 0
            fb += 40 * _score_distance(offer) / 100 if offer.get("userDistanceKm") is not None else 20
            fb += 30 * _score_discount(offer) / 100
            if offer.get("categoryName") in ESSENTIAL_CATEGORIES:
                fb += 15
            final = 0.5 * bd["finalScore"] + 0.5 * fb
            bd["finalScore"] = round(final, 1)
            bd["blended"] = True
            offer["_score"] = bd["finalScore"]
            offer["_breakdown"] = bd
            offer["_reasonLabel"] = get_offer_reason_label(bd)
    else:
        for offer in offers:
            bd = score_offer_for_user(offer, profile, history)
            offer["_score"] = bd["finalScore"]
            offer["_breakdown"] = bd
            offer["_reasonLabel"] = get_offer_reason_label(bd)

    offers.sort(
        key=lambda x: (x.get("inStock") is not False, x["_score"]),
        reverse=True,
    )

    top = offers[:20]
    rest = offers[20:]
    return diversify_ranked_offers(top) + rest, meta
