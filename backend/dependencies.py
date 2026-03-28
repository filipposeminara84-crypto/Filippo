"""Shopply - Auth helpers and shared dependencies."""
import os
import math
import random
import string
import re as re_module
import uuid
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import db

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

# Referral constants
REFERRAL_PUNTI_INVITANTE = 50
REFERRAL_PUNTI_INVITATO = 25
PUNTI_PER_EURO = 10


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token non valido")
        user = await db.utenti.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def generate_referral_code(nome: str) -> str:
    prefix = ''.join(c.upper() for c in nome[:3] if c.isalpha())
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{prefix}{suffix}"


async def create_notification(utente_id: str, tipo: str, titolo: str, messaggio: str, link: str = None, dati_extra: dict = None):
    notifica_doc = {
        "id": str(uuid.uuid4()),
        "utente_id": utente_id,
        "tipo": tipo,
        "titolo": titolo,
        "messaggio": messaggio,
        "data": datetime.now(timezone.utc).isoformat(),
        "letta": False,
        "link": link,
        "dati_extra": dati_extra
    }
    await db.notifiche.insert_one(notifica_doc)
    return notifica_doc


# Product matching helpers
_QTY_PATTERN = re_module.compile(
    r'\s+\d+\s*(ml|l|lt|cl|g|gr|kg|pz|pezzi|conf|confezione)\b\.?\s*$',
    re_module.IGNORECASE,
)
_TRAILING_NUM = re_module.compile(r'\s+\d+$')

def normalize_product_name(name: str) -> str:
    n = _QTY_PATTERN.sub('', name).strip()
    n = _TRAILING_NUM.sub('', n).strip()
    return n if n else name

def best_match_key(requested: str, prezzi_map: dict) -> str | None:
    req_lower = requested.lower()
    if req_lower in prezzi_map:
        return req_lower
    norm = normalize_product_name(requested).lower()
    if norm in prezzi_map:
        return norm
    best_key = None
    best_score = 0
    for db_key in prezzi_map:
        db_norm = normalize_product_name(db_key).lower()
        if db_norm == norm:
            return db_key
        if db_norm.startswith(norm) or norm.startswith(db_norm):
            score = len(set(norm.split()) & set(db_norm.split()))
            if score > best_score:
                best_score = score
                best_key = db_key
    if best_key:
        return best_key
    req_words = set(norm.split())
    for db_key in prezzi_map:
        db_words = set(normalize_product_name(db_key).lower().split())
        if req_words and req_words.issubset(db_words) or db_words.issubset(req_words):
            overlap = len(req_words & db_words)
            if overlap > best_score:
                best_score = overlap
                best_key = db_key
    return best_key
