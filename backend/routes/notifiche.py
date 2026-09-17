"""Notification routes."""
from typing import List
from fastapi import APIRouter, Depends
from models import Notifica
from database import db
from dependencies import get_current_user

router = APIRouter(prefix="/notifiche", tags=["notifiche"])


@router.get("", response_model=List[Notifica])
async def get_notifiche(current_user: dict = Depends(get_current_user)):
    return await db.notifiche.find({"utente_id": current_user["id"]}, {"_id": 0}).sort("data", -1).to_list(50)


@router.get("/non-lette")
async def get_notifiche_non_lette(current_user: dict = Depends(get_current_user)):
    count = await db.notifiche.count_documents({"utente_id": current_user["id"], "letta": False})
    return {"count": count}


@router.patch("/{notifica_id}/letta")
async def segna_letta(notifica_id: str, current_user: dict = Depends(get_current_user)):
    await db.notifiche.update_one({"id": notifica_id, "utente_id": current_user["id"]}, {"$set": {"letta": True}})
    return {"message": "Notifica segnata come letta"}


@router.patch("/leggi-tutte")
async def leggi_tutte(current_user: dict = Depends(get_current_user)):
    await db.notifiche.update_many({"utente_id": current_user["id"], "letta": False}, {"$set": {"letta": True}})
    return {"message": "Tutte le notifiche segnate come lette"}


@router.delete("/{notifica_id}")
async def elimina_notifica(notifica_id: str, current_user: dict = Depends(get_current_user)):
    await db.notifiche.delete_one({"id": notifica_id, "utente_id": current_user["id"]})
    return {"message": "Notifica eliminata"}
