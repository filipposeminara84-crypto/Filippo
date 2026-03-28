"""Referral program routes."""
import os
import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from models import ReferralInvito, ReferralResponse
from database import db
from dependencies import (
    get_current_user, generate_referral_code, create_notification,
    REFERRAL_PUNTI_INVITANTE, REFERRAL_PUNTI_INVITATO, PUNTI_PER_EURO,
)

router = APIRouter(prefix="/referral", tags=["referral"])


@router.get("/stats")
async def get_referral_stats(current_user: dict = Depends(get_current_user)):
    referrals = await db.referrals.find({"invitante_id": current_user["id"]}, {"_id": 0}).to_list(100)
    completati = [r for r in referrals if r["stato"] == "completed"]
    pendenti = [r for r in referrals if r["stato"] == "pending"]
    storico = [{"data": r.get("data_completamento"),
                "descrizione": f"Registrazione {r.get('invitato_email', 'utente')}",
                "punti": r.get("punti_assegnati", REFERRAL_PUNTI_INVITANTE)} for r in completati]
    punti_totali = current_user.get("punti_referral", 0)
    return {
        "referral_code": current_user.get("referral_code"),
        "punti_totali": punti_totali,
        "inviti_completati": len(completati), "inviti_pendenti": len(pendenti),
        "bonus_disponibile": round(punti_totali / PUNTI_PER_EURO, 2),
        "storico_bonus": storico,
        "punti_per_invito": REFERRAL_PUNTI_INVITANTE,
        "punti_per_registrazione": REFERRAL_PUNTI_INVITATO,
        "punti_per_euro": PUNTI_PER_EURO,
    }


@router.get("/inviti", response_model=List[ReferralResponse])
async def get_referral_inviti(current_user: dict = Depends(get_current_user)):
    return await db.referrals.find({"invitante_id": current_user["id"]}, {"_id": 0}).sort("data_invito", -1).to_list(50)


@router.post("/invita")
async def invita_referral(invito: ReferralInvito, current_user: dict = Depends(get_current_user)):
    if await db.utenti.find_one({"email": invito.email}):
        raise HTTPException(status_code=400, detail="Questo utente è già registrato")
    if await db.referrals.find_one({"invitante_id": current_user["id"], "invitato_email": invito.email}):
        raise HTTPException(status_code=400, detail="Hai già invitato questo utente")

    referral_doc = {
        "id": str(uuid.uuid4()), "invitante_id": current_user["id"],
        "invitante_nome": current_user["nome"], "invitato_email": invito.email,
        "invitato_id": None, "stato": "pending", "punti_assegnati": 0,
        "data_invito": datetime.now(timezone.utc).isoformat(), "data_completamento": None,
    }
    await db.referrals.insert_one(referral_doc)
    app_url = os.environ.get('APP_URL', '')
    return {"message": f"Invito inviato a {invito.email}",
            "referral_code": current_user.get("referral_code"),
            "link": f"{app_url}/register?ref={current_user.get('referral_code')}"}


@router.post("/genera-codice")
async def genera_codice_referral(current_user: dict = Depends(get_current_user)):
    if current_user.get("referral_code"):
        return {"referral_code": current_user["referral_code"], "message": "Codice già esistente"}
    referral_code = generate_referral_code(current_user["nome"])
    while await db.utenti.find_one({"referral_code": referral_code}):
        referral_code = generate_referral_code(current_user["nome"])
    await db.utenti.update_one({"id": current_user["id"]}, {"$set": {"referral_code": referral_code, "punti_referral": 0}})
    return {"referral_code": referral_code, "message": "Codice generato con successo"}


@router.post("/riscatta")
async def riscatta_punti(punti: int, current_user: dict = Depends(get_current_user)):
    if punti <= 0:
        raise HTTPException(status_code=400, detail="Punti non validi")
    punti_disponibili = current_user.get("punti_referral", 0)
    if punti > punti_disponibili:
        raise HTTPException(status_code=400, detail="Punti insufficienti")
    sconto_euro = punti / PUNTI_PER_EURO
    await db.utenti.update_one({"id": current_user["id"]}, {"$inc": {"punti_referral": -punti}})
    await db.riscatti_referral.insert_one({
        "id": str(uuid.uuid4()), "utente_id": current_user["id"],
        "punti_riscattati": punti, "valore_euro": sconto_euro,
        "data": datetime.now(timezone.utc).isoformat(),
    })
    await create_notification(current_user["id"], "referral", "💰 Sconto riscattato!",
        f"Hai riscattato {punti} punti per uno sconto di €{sconto_euro:.2f}", link="/referral")
    return {"message": "Punti riscattati con successo", "punti_riscattati": punti,
            "sconto_euro": round(sconto_euro, 2), "punti_rimanenti": punti_disponibili - punti}


@router.get("/classifica")
async def get_classifica_referral():
    top_users = await db.utenti.find(
        {"punti_referral": {"$gt": 0}}, {"_id": 0, "nome": 1, "punti_referral": 1}
    ).sort("punti_referral", -1).limit(10).to_list(10)
    return [{"posizione": i, "nome": u["nome"][:2] + "***", "punti": u["punti_referral"]}
            for i, u in enumerate(top_users, 1)]
