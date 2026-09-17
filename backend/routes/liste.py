"""Shopping list routes (CRUD + sharing)."""
import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from models import ListaSpesaCreate, ListaSpesa, CondividiListaRequest
from database import db
from dependencies import get_current_user, create_notification

router = APIRouter(tags=["liste"])


@router.get("/liste", response_model=List[ListaSpesa])
async def get_liste(current_user: dict = Depends(get_current_user)):
    query = {
        "$or": [
            {"utente_id": current_user["id"]},
            {"membri_condivisi": current_user["email"]},
            {"famiglia_id": current_user.get("famiglia_id")} if current_user.get("famiglia_id") else {"_id": None}
        ]
    }
    return await db.liste_spesa.find(query, {"_id": 0}).sort("data_creazione", -1).to_list(20)


@router.post("/liste", response_model=ListaSpesa)
async def create_lista(lista: ListaSpesaCreate, current_user: dict = Depends(get_current_user)):
    count = await db.liste_spesa.count_documents({"utente_id": current_user["id"]})
    if count >= 10:
        raise HTTPException(status_code=400, detail="Limite di 10 liste raggiunto")
    lista_doc = {
        "id": str(uuid.uuid4()), "utente_id": current_user["id"],
        "nome": lista.nome, "prodotti": lista.prodotti,
        "data_creazione": datetime.now(timezone.utc).isoformat(),
        "condivisa": False, "famiglia_id": current_user.get("famiglia_id"), "membri_condivisi": [],
    }
    await db.liste_spesa.insert_one(lista_doc)
    return ListaSpesa(**lista_doc)


@router.put("/liste/{lista_id}")
async def update_lista(lista_id: str, lista: ListaSpesaCreate, current_user: dict = Depends(get_current_user)):
    result = await db.liste_spesa.update_one(
        {"id": lista_id, "$or": [{"utente_id": current_user["id"]}, {"membri_condivisi": current_user["email"]}]},
        {"$set": {"nome": lista.nome, "prodotti": lista.prodotti}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Lista non trovata")
    return {"message": "Lista aggiornata"}


@router.delete("/liste/{lista_id}")
async def delete_lista(lista_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.liste_spesa.delete_one({"id": lista_id, "utente_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lista non trovata")
    return {"message": "Lista eliminata"}


@router.post("/liste/{lista_id}/condividi")
async def condividi_lista(lista_id: str, req: CondividiListaRequest, current_user: dict = Depends(get_current_user)):
    lista = await db.liste_spesa.find_one({"id": lista_id, "utente_id": current_user["id"]}, {"_id": 0})
    if not lista:
        raise HTTPException(status_code=404, detail="Lista non trovata")
    destinatario = await db.utenti.find_one({"email": req.email_destinatario}, {"_id": 0})
    await db.liste_spesa.update_one(
        {"id": lista_id},
        {"$set": {"condivisa": True}, "$addToSet": {"membri_condivisi": req.email_destinatario}}
    )
    if destinatario:
        await create_notification(destinatario["id"], "condivisione",
            f"📋 Lista condivisa da {current_user['nome']}",
            f"{current_user['nome']} ha condiviso la lista '{lista['nome']}' con te.", link=f"/liste/{lista_id}")
    return {"message": f"Lista condivisa con {req.email_destinatario}", "success": True}


@router.delete("/liste/{lista_id}/condividi/{email}")
async def rimuovi_condivisione(lista_id: str, email: str, current_user: dict = Depends(get_current_user)):
    result = await db.liste_spesa.update_one(
        {"id": lista_id, "utente_id": current_user["id"]},
        {"$pull": {"membri_condivisi": email}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Lista non trovata")
    return {"message": "Condivisione rimossa"}
