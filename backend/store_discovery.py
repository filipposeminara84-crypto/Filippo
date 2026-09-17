"""Shopply - Real supermarket discovery via OpenStreetMap Overpass API."""
import re
import logging
import urllib.parse
import httpx
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

KNOWN_CHAINS = {
    "esselunga": "Esselunga", "la esse": "Esselunga", "laesse": "Esselunga",
    "coop": "Coop", "ipercoop": "Ipercoop", "incoop": "Coop",
    "conad": "Conad", "conad city": "Conad", "conad superstore": "Conad", "spazio conad": "Conad",
    "carrefour": "Carrefour", "carrefour market": "Carrefour", "carrefour express": "Carrefour",
    "lidl": "Lidl",
    "eurospin": "Eurospin",
    "aldi": "Aldi",
    "md": "MD", "md discount": "MD",
    "penny": "Penny", "penny market": "Penny",
    "despar": "Despar", "interspar": "Despar", "eurospar": "Despar",
    "unes": "Unes", "u2": "Unes", "u! come tu mi vuoi": "Unes",
    "il gigante": "Il Gigante",
    "deco": "Deco", "decò": "Deco",
    "sigma": "Sigma",
    "pam": "Pam", "pam local": "Pam", "panorama": "Pam",
    "bennet": "Bennet",
    "famila": "Famila",
    "a&o": "A&O", "super a&o": "A&O",
    "todis": "Todis",
    "simply": "Simply", "punto simply": "Simply", "punto sma": "Simply",
    "sma": "Simply",
    "tigros": "Tigros",
    "iper": "Iper", "la grande i": "Iper",
    "crai": "Crai",
    "naturasì": "NaturaSi",
    "naturasi": "NaturaSi",
    "in's": "iN's", "in's mercato": "iN's", "ins": "iN's",
    "dpiu": "DPiu", "dpiù": "DPiu", "d+": "DPiu", "d più": "DPiu", "d piu": "DPiu",
    "pewex": "Pewex",
    "iperal": "Iperal",
    "to.market": "to.market",
    "tigre": "Tigre",
    "dok": "Dok",
    "tuodi'": "Tuodi", "tuodì": "Tuodi", "tuodi": "Tuodi",
    "risparmio casa": "Risparmio Casa",
    "ekom": "Ekom",
    "ali": "Ali",
    "alì": "Ali",
    "aliper": "Ali",
    "prix": "Prix",
}

_CHAIN_KEYS = sorted(KNOWN_CHAINS.keys(), key=len, reverse=True)

NON_SUPERMARKET_PATTERNS = [
    "tigotà", "tigota", "acqua & sapone", "acqua e sapone", "caddy",
    "cash & carry", "cash and carry", "cash&carry", "c+c",
    "centro commerciale", "centro servizi", "home & fashion",
]


def _is_excluded(name: str, brand: str = "", operator: str = "") -> bool:
    """True if the POI is not a real grocery supermarket (drugstore, mall, wholesale)."""
    text = " ".join(filter(None, [name, brand, operator])).lower()
    return any(p in text for p in NON_SUPERMARKET_PATTERNS)


def _word_match(key: str, text: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", text) is not None


def _identify_chain(name: str, brand: str = None, operator: str = None) -> str:
    sources = [s.lower().strip() for s in [brand, operator, name] if s]
    for lower in sources:
        if lower in KNOWN_CHAINS:
            return KNOWN_CHAINS[lower]
    for lower in sources:
        for key in _CHAIN_KEYS:
            if _word_match(key, lower):
                return KNOWN_CHAINS[key]
    return name.strip() if name else "Altro"


def _make_store_id(name: str, osm_id: int) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower().strip()).strip('-')[:30]
    return f"osm-{slug}-{osm_id}"


async def _query_overpass(query: str, per_mirror_timeout: float = 12.0, total_budget_s: float = 30.0) -> dict | None:
    """Try each Overpass mirror until one responds, within a total time budget."""
    import time
    encoded = urllib.parse.quote(query)
    start = time.monotonic()
    for base in OVERPASS_MIRRORS:
        if time.monotonic() - start > total_budget_s:
            logger.warning("[Overpass] Total time budget exhausted")
            break
        url = f"{base}?data={encoded}"
        try:
            async with httpx.AsyncClient(timeout=per_mirror_timeout) as client:
                resp = await client.get(url, headers={"User-Agent": "Shopply/1.0"})
                if resp.status_code == 200:
                    data = resp.json()
                    if "elements" in data:
                        logger.info(f"[Overpass] Success via {base}")
                        return data
                logger.warning(f"[Overpass] {base} -> HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"[Overpass] {base} failed: {type(e).__name__}")
    return None


async def discover_stores_overpass(lat: float, lng: float, radius_m: int = 15000) -> list[dict]:
    query = (
        f'[out:json][timeout:20];'
        f'(node["shop"="supermarket"](around:{radius_m},{lat},{lng});'
        f'way["shop"="supermarket"](around:{radius_m},{lat},{lng}););'
        f'out center body;'
    )
    data = await _query_overpass(query)
    if data is None:
        logger.error("[Overpass] All mirrors failed")
        return []

    stores = []
    seen_ids = set()

    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name", "").strip()
        if not name:
            continue

        brand = tags.get("brand", "")
        operator = tags.get("operator", "")

        if _is_excluded(name, brand, operator):
            continue

        if el["type"] == "node":
            s_lat, s_lng = el.get("lat"), el.get("lon")
        else:
            center = el.get("center", {})
            s_lat, s_lng = center.get("lat"), center.get("lon")

        if not s_lat or not s_lng:
            continue

        osm_id = el.get("id", 0)
        store_id = _make_store_id(name, osm_id)
        if store_id in seen_ids:
            continue
        seen_ids.add(store_id)

        chain = _identify_chain(name, brand, operator)

        addr_parts = []
        street = tags.get("addr:street", "")
        housenumber = tags.get("addr:housenumber", "")
        city = tags.get("addr:city", tags.get("addr:suburb", ""))
        postcode = tags.get("addr:postcode", "")
        if street:
            addr_parts.append(f"{street} {housenumber}".strip())
        if postcode:
            addr_parts.append(postcode)
        if city:
            addr_parts.append(city)
        indirizzo = ", ".join(addr_parts) if addr_parts else ""

        phone = tags.get("phone", tags.get("contact:phone", ""))
        opening_hours = tags.get("opening_hours", "")
        orari = {"info": opening_hours} if opening_hours else {}

        stores.append({
            "id": store_id,
            "nome": name,
            "catena": chain,
            "indirizzo": indirizzo,
            "lat": round(s_lat, 6),
            "lng": round(s_lng, 6),
            "orari": orari,
            "telefono": phone,
            "servizi": [],
            "fonte": "osm",
            "osm_id": osm_id,
            "citta": city or "",
            "regione": "",
            "scoperto_il": datetime.now(timezone.utc).isoformat(),
        })

    logger.info(f"[Overpass] Found {len(stores)} supermarkets within {radius_m/1000:.0f}km of ({lat}, {lng})")
    return stores
