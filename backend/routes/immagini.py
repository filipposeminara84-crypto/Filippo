"""Product image routes - Open Food Facts integration."""
import httpx
import logging
from fastapi import APIRouter
from database import db

router = APIRouter(prefix="/prodotti", tags=["immagini"])
logger = logging.getLogger(__name__)

OFF_API = "https://it.openfoodfacts.org/api/v2/search"
OFF_FIELDS = "product_name,brands,image_front_small_url,image_front_url,quantity"


@router.get("/immagine")
async def get_product_image(q: str):
    """Search Open Food Facts for a product image. Results are cached in DB."""
    q_lower = q.strip().lower()

    # Check cache first
    cached = await db.product_images.find_one({"query": q_lower}, {"_id": 0})
    if cached:
        return cached

    # Search Open Food Facts
    result = {"query": q_lower, "nome": q, "brand": None, "formato": None, "image_url": None}

    # Also try to get brand/format from our own DB
    local = await db.prodotti.find_one(
        {"nome_prodotto": {"$regex": q_lower.replace(" ", ".*"), "$options": "i"}},
        {"_id": 0, "brand": 1, "formato": 1, "nome_prodotto": 1}
    )
    if local:
        result["brand"] = local.get("brand")
        result["formato"] = local.get("formato")
        result["nome"] = local.get("nome_prodotto", q)

    try:
        search_query = q
        if local and local.get("brand"):
            search_query = f"{q} {local['brand']}"
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(OFF_API, params={
                "q": search_query, "fields": OFF_FIELDS, "page_size": 5, "sort_by": "popularity",
            })
            if resp.status_code == 200:
                data = resp.json()
                products = data.get("products", [])
                for p in products:
                    img = p.get("image_front_small_url") or p.get("image_front_url")
                    if img:
                        result["image_url"] = img
                        if not result["brand"]:
                            result["brand"] = p.get("brands")
                        if not result["formato"]:
                            result["formato"] = p.get("quantity")
                        break
                # If no product had an image, try without brand
                if not result["image_url"] and search_query != q:
                    resp2 = await client.get(OFF_API, params={
                        "q": q, "fields": OFF_FIELDS, "page_size": 5, "sort_by": "popularity",
                    })
                    if resp2.status_code == 200:
                        for p in resp2.json().get("products", []):
                            img = p.get("image_front_small_url") or p.get("image_front_url")
                            if img:
                                result["image_url"] = img
                                break
    except Exception as e:
        logger.warning(f"Open Food Facts error for '{q}': {e}")

    # Cache the result
    await db.product_images.update_one(
        {"query": q_lower}, {"$set": result}, upsert=True
    )
    return result
