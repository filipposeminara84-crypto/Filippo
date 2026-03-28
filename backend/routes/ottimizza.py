"""Optimization engine + price matrix + price update routes."""
import uuid
import random
import re as re_module
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from models import (
    OttimizzaRequest, OttimizzaResponse, ProdottoAssegnato, SupermercatoPercorso,
    Supermercato, RicercaStorica,
)
from database import db
from dependencies import (
    get_current_user, haversine_distance, create_notification,
    normalize_product_name, best_match_key,
)

router = APIRouter(tags=["ottimizza"])


@router.post("/ottimizza", response_model=OttimizzaResponse)
async def ottimizza_spesa(req: OttimizzaRequest, current_user: dict = Depends(get_current_user)):
    supermercati = await db.supermercati.find({}, {"_id": 0}).to_list(100)
    supermercati_vicini = []
    for sup in supermercati:
        dist = haversine_distance(req.lat_utente, req.lng_utente, sup["lat"], sup["lng"])
        if dist <= req.raggio_km:
            sup["distanza"] = dist
            supermercati_vicini.append(sup)
    if not supermercati_vicini:
        raise HTTPException(status_code=400, detail="Nessun supermercato trovato nel raggio specificato")

    # FUZZY MATCHING: Build regex patterns from normalized product names
    regex_parts = list(dict.fromkeys(re_module.escape(normalize_product_name(p)) for p in req.lista_prodotti))
    prodotti_db = await db.prodotti.find(
        {"nome_prodotto": {"$regex": f"({'|'.join(regex_parts)})", "$options": "i"}},
        {"_id": 0, "nome_prodotto": 1, "supermercato_id": 1, "prezzo": 1, "in_offerta": 1}
    ).to_list(1000)

    prezzi_map = {}
    for prod in prodotti_db:
        nome = prod["nome_prodotto"].lower()
        if nome not in prezzi_map:
            prezzi_map[nome] = {}
        prezzi_map[nome][prod["supermercato_id"]] = {
            "prezzo": prod["prezzo"], "in_offerta": prod.get("in_offerta", False),
        }

    assegnazioni = {}
    costo_totale = 0.0
    costo_peggiore = 0.0
    prodotti_non_trovati = []

    for prodotto_richiesto in req.lista_prodotti:
        matched_key = best_match_key(prodotto_richiesto, prezzi_map)
        if matched_key is None:
            prodotti_non_trovati.append(prodotto_richiesto)
            continue

        miglior_score = float('inf')
        miglior_sup_id = None
        miglior_prezzo = 0
        miglior_in_offerta = False
        prezzo_max = 0

        for sup in supermercati_vicini:
            if sup["id"] not in prezzi_map[matched_key]:
                continue
            info_prezzo = prezzi_map[matched_key][sup["id"]]
            prezzo = info_prezzo["prezzo"]
            distanza = sup["distanza"]
            score = (req.peso_prezzo * prezzo / 10) + (req.peso_tempo * distanza / req.raggio_km)
            if score < miglior_score:
                miglior_score = score
                miglior_sup_id = sup["id"]
                miglior_prezzo = prezzo
                miglior_in_offerta = info_prezzo["in_offerta"]
            if prezzo > prezzo_max:
                prezzo_max = prezzo

        if miglior_sup_id:
            if miglior_sup_id not in assegnazioni:
                assegnazioni[miglior_sup_id] = []
            assegnazioni[miglior_sup_id].append({
                "prodotto": prodotto_richiesto, "prezzo": miglior_prezzo, "in_offerta": miglior_in_offerta,
            })
            costo_totale += miglior_prezzo
            costo_peggiore += prezzo_max if prezzo_max > 0 else miglior_prezzo

    if len(assegnazioni) > req.max_supermercati:
        sorted_sups = sorted(assegnazioni.items(), key=lambda x: len(x[1]), reverse=True)
        kept_stores = dict(sorted_sups[:req.max_supermercati])
        kept_store_ids = set(kept_stores.keys())
        for _, dropped_products in sorted_sups[req.max_supermercati:]:
            for prod_info in dropped_products:
                prodotto_lower = prod_info["prodotto"].lower()
                best_price = float('inf')
                best_kept_id = None
                for kept_id in kept_store_ids:
                    if prodotto_lower in prezzi_map and kept_id in prezzi_map[prodotto_lower]:
                        p = prezzi_map[prodotto_lower][kept_id]["prezzo"]
                        if p < best_price:
                            best_price = p
                            best_kept_id = kept_id
                if best_kept_id:
                    kept_stores[best_kept_id].append({
                        "prodotto": prod_info["prodotto"], "prezzo": best_price,
                        "in_offerta": prezzi_map.get(prodotto_lower, {}).get(best_kept_id, {}).get("in_offerta", False),
                    })
                else:
                    first_kept = list(kept_store_ids)[0]
                    kept_stores[first_kept].append(prod_info)
        assegnazioni = kept_stores
        costo_totale = sum(p["prezzo"] for prods in assegnazioni.values() for p in prods)

    # Build route (nearest-neighbor TSP)
    piano = []
    pos_corrente = (req.lat_utente, req.lng_utente)
    sup_rimanenti = list(assegnazioni.keys())
    distanza_totale = 0.0
    ordine = 1
    while sup_rimanenti:
        min_dist = float('inf')
        prossimo_sup_id = None
        for sup_id in sup_rimanenti:
            sup = next(s for s in supermercati_vicini if s["id"] == sup_id)
            dist = haversine_distance(pos_corrente[0], pos_corrente[1], sup["lat"], sup["lng"])
            if dist < min_dist:
                min_dist = dist
                prossimo_sup_id = sup_id
        sup_data = next(s for s in supermercati_vicini if s["id"] == prossimo_sup_id)
        prodotti_assegnati = [
            ProdottoAssegnato(prodotto=p["prodotto"], supermercato_id=prossimo_sup_id,
                              supermercato_nome=sup_data["nome"], prezzo=p["prezzo"], in_offerta=p["in_offerta"])
            for p in assegnazioni[prossimo_sup_id]
        ]
        piano.append(SupermercatoPercorso(
            supermercato=Supermercato(**sup_data), prodotti=prodotti_assegnati,
            subtotale=sum(p["prezzo"] for p in assegnazioni[prossimo_sup_id]), ordine=ordine,
        ))
        distanza_totale += min_dist
        pos_corrente = (sup_data["lat"], sup_data["lng"])
        sup_rimanenti.remove(prossimo_sup_id)
        ordine += 1

    tempo_totale = int(distanza_totale / 30 * 60) + (len(piano) * 10)
    risparmio = max(0, costo_peggiore - costo_totale)
    risparmio_perc = (risparmio / costo_peggiore * 100) if costo_peggiore > 0 else 0

    storico_doc = {
        "id": str(uuid.uuid4()), "utente_id": current_user["id"],
        "timestamp": datetime.now(timezone.utc).isoformat(), "input_lista": req.lista_prodotti,
        "costo_totale": round(costo_totale, 2), "tempo_totale_min": tempo_totale,
        "risparmio": round(risparmio, 2), "num_supermercati": len(piano), "eseguita": False,
    }
    await db.ricerche_storiche.insert_one(storico_doc)
    await db.utenti.update_one(
        {"id": current_user["id"]},
        {"$inc": {"statistiche.spese_totali": 1, "statistiche.risparmio_totale_euro": round(risparmio, 2)}}
    )

    return OttimizzaResponse(
        piano_ottimale=piano, costo_totale=round(costo_totale, 2), tempo_stimato_min=tempo_totale,
        risparmio_euro=round(risparmio, 2), risparmio_percentuale=round(risparmio_perc, 1),
        num_supermercati=len(piano), distanza_totale_km=round(distanza_totale, 2),
        prodotti_non_trovati=prodotti_non_trovati,
    )


# ============== STORICO ==============

@router.get("/storico", response_model=List[RicercaStorica])
async def get_storico(current_user: dict = Depends(get_current_user)):
    return await db.ricerche_storiche.find({"utente_id": current_user["id"]}, {"_id": 0}).sort("timestamp", -1).to_list(10)

@router.patch("/storico/{ricerca_id}/eseguita")
async def mark_eseguita(ricerca_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.ricerche_storiche.update_one(
        {"id": ricerca_id, "utente_id": current_user["id"]}, {"$set": {"eseguita": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ricerca non trovata")
    return {"message": "Ricerca segnata come eseguita"}


# ============== MATRICE PREZZI ==============

@router.post("/matrice-prezzi")
async def get_matrice_prezzi(prodotti: List[str]):
    result = {}
    for prodotto in prodotti:
        norm = normalize_product_name(prodotto)
        escaped = re_module.escape(norm)
        prezzi_prodotto = await db.prodotti.find(
            {"nome_prodotto": {"$regex": escaped, "$options": "i"}},
            {"_id": 0, "supermercato_id": 1, "prezzo": 1, "in_offerta": 1, "sconto_percentuale": 1}
        ).to_list(100)
        result[prodotto] = {
            p["supermercato_id"]: {"prezzo": p["prezzo"], "in_offerta": p.get("in_offerta", False),
                                    "sconto": p.get("sconto_percentuale")}
            for p in prezzi_prodotto
        }
    return result


# ============== AGGIORNAMENTO PREZZI ==============

@router.post("/prezzi/aggiorna")
async def aggiorna_prezzi_manuale(background_tasks: BackgroundTasks):
    background_tasks.add_task(aggiorna_prezzi_task)
    return {"message": "Aggiornamento prezzi avviato in background"}

async def aggiorna_prezzi_task():
    from pymongo import UpdateOne
    prodotti = await db.prodotti.find(
        {}, {"_id": 0, "id": 1, "nome_prodotto": 1, "prezzo": 1, "supermercato_id": 1}
    ).to_list(5000)

    operations = []
    nuove_offerte = []
    for prod in prodotti:
        prezzo_attuale = prod["prezzo"]
        variazione = random.uniform(-0.05, 0.03)
        nuovo_prezzo = round(prezzo_attuale * (1 + variazione), 2)
        in_offerta = random.random() < 0.10
        sconto = None
        if in_offerta:
            sconto = random.choice([10, 15, 20, 25, 30])
            nuovo_prezzo = round(prezzo_attuale * (1 - sconto/100), 2)
            nuove_offerte.append({
                "prodotto": prod["nome_prodotto"], "supermercato_id": prod["supermercato_id"],
                "sconto": sconto, "prezzo_nuovo": nuovo_prezzo, "prezzo_vecchio": prezzo_attuale,
            })
        operations.append(UpdateOne(
            {"id": prod["id"]},
            {"$set": {"prezzo": nuovo_prezzo, "prezzo_precedente": prezzo_attuale,
                      "in_offerta": in_offerta, "sconto_percentuale": sconto,
                      "data_aggiornamento": datetime.now(timezone.utc).isoformat()}}
        ))
    if operations:
        await db.prodotti.bulk_write(operations)

    if nuove_offerte:
        users = await db.utenti.find(
            {"preferenze.notifiche_offerte": True}, {"_id": 0, "id": 1}
        ).limit(500).to_list(500)
        top_offerte = sorted(nuove_offerte, key=lambda x: x["sconto"], reverse=True)[:5]
        for user in users:
            await create_notification(
                user["id"], "offerta",
                f"🔥 {len(nuove_offerte)} nuove offerte disponibili!",
                f"Scopri sconti fino al {top_offerte[0]['sconto']}% su {top_offerte[0]['prodotto']}",
                link="/offerte", dati_extra={"offerte_count": len(nuove_offerte)}
            )
    await db.aggiornamenti_prezzi.insert_one({
        "id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(),
        "prodotti_aggiornati": len(operations), "nuove_offerte": len(nuove_offerte),
    })

@router.get("/prezzi/ultimo-aggiornamento")
async def ultimo_aggiornamento():
    ultimo = await db.aggiornamenti_prezzi.find_one({}, {"_id": 0}, sort=[("timestamp", -1)])
    return ultimo or {"message": "Nessun aggiornamento"}
