"""Auth routes: register, login, me, password reset."""
import os
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from models import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    PasswordResetRequest, PasswordResetConfirm,
)
from database import db
from dependencies import (
    hash_password, verify_password, create_token, get_current_user,
    generate_referral_code, create_notification,
    REFERRAL_PUNTI_INVITANTE, REFERRAL_PUNTI_INVITATO,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.utenti.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")

    user_id = str(uuid.uuid4())
    referral_code = generate_referral_code(user_data.nome)
    while await db.utenti.find_one({"referral_code": referral_code}):
        referral_code = generate_referral_code(user_data.nome)

    invitante = None
    punti_iniziali = 0
    if user_data.referral_code:
        invitante = await db.utenti.find_one({"referral_code": user_data.referral_code.upper()}, {"_id": 0})
        if invitante:
            punti_iniziali = REFERRAL_PUNTI_INVITATO

    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "nome": user_data.nome,
        "password_hash": hash_password(user_data.password),
        "data_registrazione": datetime.now(timezone.utc).isoformat(),
        "preferenze": {
            "raggio_max_km": 5, "max_supermercati": 3, "peso_prezzo": 0.7, "peso_tempo": 0.3,
            "supermercati_preferiti": [], "notifiche_offerte": True, "notifiche_condivisione": True,
        },
        "statistiche": {"spese_totali": 0, "risparmio_totale_euro": 0.0, "tempo_totale_risparmiato_min": 0},
        "famiglia_id": None,
        "referral_code": referral_code,
        "punti_referral": punti_iniziali,
        "invitato_da": invitante["id"] if invitante else None,
    }
    await db.utenti.insert_one(user_doc)

    await create_notification(user_id, "sistema", "Benvenuto su Shopply! 🛒",
        "Inizia ad aggiungere prodotti alla tua lista per ottimizzare la spesa.")

    if invitante:
        await db.utenti.update_one({"id": invitante["id"]}, {"$inc": {"punti_referral": REFERRAL_PUNTI_INVITANTE}})
        await db.referrals.update_one(
            {"invitante_id": invitante["id"], "invitato_email": user_data.email},
            {"$set": {"stato": "completed", "invitato_id": user_id,
                      "punti_assegnati": REFERRAL_PUNTI_INVITANTE,
                      "data_completamento": datetime.now(timezone.utc).isoformat()}}
        )
        await create_notification(invitante["id"], "referral",
            f"🎉 {user_data.nome} si è registrato!",
            f"Hai guadagnato {REFERRAL_PUNTI_INVITANTE} punti grazie al tuo invito!", link="/referral")
        await create_notification(user_id, "referral", "🎁 Bonus di benvenuto!",
            f"Hai ricevuto {REFERRAL_PUNTI_INVITATO} punti grazie all'invito di {invitante['nome']}!", link="/referral")

    token = create_token(user_id)
    user_response = UserResponse(
        id=user_id, email=user_data.email, nome=user_data.nome,
        data_registrazione=user_doc["data_registrazione"],
        preferenze=user_doc["preferenze"], statistiche=user_doc["statistiche"],
        referral_code=referral_code, punti_referral=punti_iniziali,
    )
    return TokenResponse(access_token=token, user=user_response)


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    user = await db.utenti.find_one({"email": login_data.email}, {"_id": 0})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenziali non valide")

    token = create_token(user["id"])
    user_response = UserResponse(
        id=user["id"], email=user["email"], nome=user["nome"],
        data_registrazione=user["data_registrazione"],
        preferenze=user["preferenze"], statistiche=user["statistiche"],
        famiglia_id=user.get("famiglia_id"),
        referral_code=user.get("referral_code"),
        punti_referral=user.get("punti_referral", 0),
    )
    return TokenResponse(access_token=token, user=user_response)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"], email=current_user["email"], nome=current_user["nome"],
        data_registrazione=current_user["data_registrazione"],
        preferenze=current_user["preferenze"], statistiche=current_user["statistiche"],
        famiglia_id=current_user.get("famiglia_id"),
        referral_code=current_user.get("referral_code"),
        punti_referral=current_user.get("punti_referral", 0),
    )


@router.post("/forgot-password")
async def forgot_password(req: PasswordResetRequest):
    user = await db.utenti.find_one({"email": req.email}, {"_id": 0})
    if not user:
        return {"message": "Se l'email esiste, riceverai un link per reimpostare la password"}

    reset_token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)

    await db.password_resets.delete_many({"email": req.email})
    await db.password_resets.insert_one({
        "id": str(uuid.uuid4()), "email": req.email,
        "token": reset_token, "expiry": expiry.isoformat(), "used": False,
    })

    app_url = os.environ.get('APP_URL', '')
    reset_link = f"{app_url}/reset-password?token={reset_token}"

    await create_notification(user["id"], "sistema", "🔐 Richiesta reset password",
        "Clicca qui per reimpostare la password. Il link scade tra 1 ora.",
        link=f"/reset-password?token={reset_token}")

    print(f"[PASSWORD RESET] Email: {req.email}, Link: {reset_link}")
    return {"message": "Se l'email esiste, riceverai un link per reimpostare la password", "demo_token": reset_token}


@router.post("/reset-password")
async def reset_password(req: PasswordResetConfirm):
    reset_record = await db.password_resets.find_one({"token": req.token, "used": False}, {"_id": 0})
    if not reset_record:
        raise HTTPException(status_code=400, detail="Token non valido o scaduto")

    expiry = datetime.fromisoformat(reset_record["expiry"])
    if datetime.now(timezone.utc) > expiry:
        raise HTTPException(status_code=400, detail="Token scaduto. Richiedi un nuovo link.")

    new_hash = hash_password(req.new_password)
    result = await db.utenti.update_one({"email": reset_record["email"]}, {"$set": {"password_hash": new_hash}})
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Errore durante il reset")

    await db.password_resets.update_one({"token": req.token}, {"$set": {"used": True}})
    user = await db.utenti.find_one({"email": reset_record["email"]}, {"_id": 0})
    if user:
        await create_notification(user["id"], "sistema", "✅ Password modificata",
            "La tua password è stata reimpostata con successo.")
    return {"message": "Password reimpostata con successo. Ora puoi accedere."}


@router.get("/verify-reset-token")
async def verify_reset_token(token: str):
    reset_record = await db.password_resets.find_one({"token": token, "used": False}, {"_id": 0})
    if not reset_record:
        return {"valid": False, "message": "Token non valido"}
    expiry = datetime.fromisoformat(reset_record["expiry"])
    if datetime.now(timezone.utc) > expiry:
        return {"valid": False, "message": "Token scaduto"}
    return {"valid": True, "email": reset_record["email"][:3] + "***"}
