"""Family routes."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from models import InvitoFamiglia
from database import db
from dependencies import get_current_user, create_notification

router = APIRouter(prefix="/famiglia", tags=["famiglia"])


@router.post("/crea")
async def crea_famiglia(nome: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("famiglia_id"):
        raise HTTPException(status_code=400, detail="Sei già in una famiglia")
    famiglia_id = str(uuid.uuid4())
    famiglia_doc = {
        "id": famiglia_id, "nome": nome, "creatore_id": current_user["id"],
        "membri": [{"id": current_user["id"], "nome": current_user["nome"],
                     "email": current_user["email"], "ruolo": "admin"}],
        "data_creazione": datetime.now(timezone.utc).isoformat(),
    }
    await db.famiglie.insert_one(famiglia_doc)
    await db.utenti.update_one({"id": current_user["id"]}, {"$set": {"famiglia_id": famiglia_id}})
    return {"message": "Famiglia creata", "famiglia_id": famiglia_id}


@router.post("/invita")
async def invita_membro(invito: InvitoFamiglia, current_user: dict = Depends(get_current_user)):
    if not current_user.get("famiglia_id"):
        raise HTTPException(status_code=400, detail="Non sei in una famiglia")
    invitato = await db.utenti.find_one({"email": invito.email}, {"_id": 0})
    invite_doc = {
        "id": str(uuid.uuid4()), "famiglia_id": current_user["famiglia_id"],
        "invitante_id": current_user["id"], "invitante_nome": current_user["nome"],
        "email_invitato": invito.email, "stato": "pending",
        "data": datetime.now(timezone.utc).isoformat(),
    }
    await db.inviti_famiglia.insert_one(invite_doc)
    if invitato:
        await create_notification(invitato["id"], "condivisione",
            f"👨‍👩‍👧‍👦 Invito famiglia da {current_user['nome']}",
            "Sei stato invitato a unirti alla famiglia. Vai nelle impostazioni per accettare.",
            link="/impostazioni")
    return {"message": f"Invito inviato a {invito.email}"}


@router.get("/inviti")
async def get_inviti(current_user: dict = Depends(get_current_user)):
    return await db.inviti_famiglia.find(
        {"email_invitato": current_user["email"], "stato": "pending"}, {"_id": 0}
    ).to_list(10)


@router.post("/inviti/{invito_id}/accetta")
async def accetta_invito(invito_id: str, current_user: dict = Depends(get_current_user)):
    invito = await db.inviti_famiglia.find_one({"id": invito_id, "email_invitato": current_user["email"]}, {"_id": 0})
    if not invito:
        raise HTTPException(status_code=404, detail="Invito non trovato")
    await db.famiglie.update_one(
        {"id": invito["famiglia_id"]},
        {"$push": {"membri": {"id": current_user["id"], "nome": current_user["nome"],
                               "email": current_user["email"], "ruolo": "membro"}}}
    )
    await db.utenti.update_one({"id": current_user["id"]}, {"$set": {"famiglia_id": invito["famiglia_id"]}})
    await db.inviti_famiglia.update_one({"id": invito_id}, {"$set": {"stato": "accepted"}})
    return {"message": "Sei entrato nella famiglia!"}


@router.get("")
async def get_famiglia(current_user: dict = Depends(get_current_user)):
    if not current_user.get("famiglia_id"):
        return None
    return await db.famiglie.find_one({"id": current_user["famiglia_id"]}, {"_id": 0})
