"""Supermarket and product routes."""
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from models import Supermercato, Prodotto, Preferenze
from database import db
from dependencies import get_current_user

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
    supermercati = await db.supermercati.find({}, {"_id": 0}).to_list(200)
    risultati = []
    for sup in supermercati:
        dist = math.sqrt(
            ((sup["lat"] - lat) * 111.32) ** 2 +
            ((sup["lng"] - lng) * 111.32 * math.cos(math.radians(lat))) ** 2
        )
        if dist <= raggio_km:
            sup["distanza_km"] = round(dist, 1)
            risultati.append(sup)
    risultati.sort(key=lambda x: x["distanza_km"])
    return risultati

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
