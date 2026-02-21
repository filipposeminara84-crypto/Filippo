from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import math
import random
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'shopply_secret_key_2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

app = FastAPI(title="Shopply API", version="2.0.0")
api_router = APIRouter(prefix="/api")

# ============== MODELS ==============

class UserBase(BaseModel):
    email: EmailStr
    nome: str

class UserCreate(UserBase):
    password: str
    referral_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    data_registrazione: str
    preferenze: Dict[str, Any]
    statistiche: Dict[str, Any]
    famiglia_id: Optional[str] = None
    referral_code: Optional[str] = None
    punti_referral: int = 0

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class Preferenze(BaseModel):
    raggio_max_km: int = 5
    max_supermercati: int = 3
    peso_prezzo: float = 0.7
    peso_tempo: float = 0.3
    supermercati_preferiti: List[str] = []
    notifiche_offerte: bool = True
    notifiche_condivisione: bool = True

class Supermercato(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nome: str
    catena: str
    indirizzo: str
    lat: float
    lng: float
    orari: Dict[str, str]
    telefono: str
    servizi: List[str]

class Prodotto(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nome_prodotto: str
    categoria: str
    brand: str
    formato: str
    supermercato_id: str
    prezzo: float
    prezzo_precedente: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    in_offerta: bool = False
    sconto_percentuale: Optional[int] = None
    data_aggiornamento: str

class ListaSpesaCreate(BaseModel):
    nome: str
    prodotti: List[str]

class ListaSpesa(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    utente_id: str
    nome: str
    prodotti: List[str]
    data_creazione: str
    condivisa: bool = False
    famiglia_id: Optional[str] = None
    membri_condivisi: List[str] = []

class OttimizzaRequest(BaseModel):
    lista_prodotti: List[str]
    lat_utente: float
    lng_utente: float
    raggio_km: int = 5
    max_supermercati: int = 3
    peso_prezzo: float = 0.7
    peso_tempo: float = 0.3

class ProdottoAssegnato(BaseModel):
    prodotto: str
    supermercato_id: str
    supermercato_nome: str
    prezzo: float
    in_offerta: bool = False

class SupermercatoPercorso(BaseModel):
    supermercato: Supermercato
    prodotti: List[ProdottoAssegnato]
    subtotale: float
    ordine: int

class OttimizzaResponse(BaseModel):
    piano_ottimale: List[SupermercatoPercorso]
    costo_totale: float
    tempo_stimato_min: int
    risparmio_euro: float
    risparmio_percentuale: float
    num_supermercati: int
    distanza_totale_km: float

class RicercaStorica(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    utente_id: str
    timestamp: str
    input_lista: List[str]
    costo_totale: float
    tempo_totale_min: int
    risparmio: float
    num_supermercati: int
    eseguita: bool = False

# ============== NEW MODELS FOR FEATURES ==============

class Notifica(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    utente_id: str
    tipo: str  # "offerta", "condivisione", "sistema", "referral"
    titolo: str
    messaggio: str
    data: str
    letta: bool = False
    link: Optional[str] = None
    dati_extra: Optional[Dict[str, Any]] = None

# ============== REFERRAL MODELS ==============

class ReferralStats(BaseModel):
    referral_code: str
    punti_totali: int
    inviti_completati: int
    inviti_pendenti: int
    bonus_disponibile: float
    storico_bonus: List[Dict[str, Any]]

class ReferralInvito(BaseModel):
    email: EmailStr

class ReferralResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    invitante_id: str
    invitante_nome: str
    invitato_email: str
    invitato_id: Optional[str] = None
    stato: str  # "pending", "completed", "expired"
    punti_assegnati: int
    data_invito: str
    data_completamento: Optional[str] = None

class InvitoFamiglia(BaseModel):
    email: EmailStr

class FamigliaResponse(BaseModel):
    id: str
    nome: str
    creatore_id: str
    membri: List[Dict[str, str]]
    data_creazione: str

class CondividiListaRequest(BaseModel):
    lista_id: str
    email_destinatario: EmailStr

# ============== AUTH HELPERS ==============

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

# ============== GEO HELPERS ==============

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ============== REFERRAL HELPERS ==============

def generate_referral_code(nome: str) -> str:
    """Genera un codice referral unico basato sul nome"""
    import string
    prefix = ''.join(c.upper() for c in nome[:3] if c.isalpha())
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{prefix}{suffix}"

# Costanti referral
REFERRAL_PUNTI_INVITANTE = 50  # Punti per chi invita
REFERRAL_PUNTI_INVITATO = 25   # Punti per chi si registra
PUNTI_PER_EURO = 10            # 10 punti = 1€ di sconto

# ============== AUTH ENDPOINTS ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.utenti.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    user_id = str(uuid.uuid4())
    referral_code = generate_referral_code(user_data.nome)
    
    # Check if unique referral code
    while await db.utenti.find_one({"referral_code": referral_code}):
        referral_code = generate_referral_code(user_data.nome)
    
    # Check if registered with referral code
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
            "raggio_max_km": 5,
            "max_supermercati": 3,
            "peso_prezzo": 0.7,
            "peso_tempo": 0.3,
            "supermercati_preferiti": [],
            "notifiche_offerte": True,
            "notifiche_condivisione": True
        },
        "statistiche": {
            "spese_totali": 0,
            "risparmio_totale_euro": 0.0,
            "tempo_totale_risparmiato_min": 0
        },
        "famiglia_id": None,
        "referral_code": referral_code,
        "punti_referral": punti_iniziali,
        "invitato_da": invitante["id"] if invitante else None
    }
    await db.utenti.insert_one(user_doc)
    
    # Create welcome notification
    await create_notification(user_id, "sistema", "Benvenuto su Shopply! 🛒", 
        "Inizia ad aggiungere prodotti alla tua lista per ottimizzare la spesa.")
    
    # If registered with referral, reward inviter
    if invitante:
        # Update inviter points
        await db.utenti.update_one(
            {"id": invitante["id"]},
            {"$inc": {"punti_referral": REFERRAL_PUNTI_INVITANTE}}
        )
        
        # Update referral record
        await db.referrals.update_one(
            {"invitante_id": invitante["id"], "invitato_email": user_data.email},
            {"$set": {
                "stato": "completed",
                "invitato_id": user_id,
                "punti_assegnati": REFERRAL_PUNTI_INVITANTE,
                "data_completamento": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Notify inviter
        await create_notification(
            invitante["id"], "referral",
            f"🎉 {user_data.nome} si è registrato!",
            f"Hai guadagnato {REFERRAL_PUNTI_INVITANTE} punti grazie al tuo invito!",
            link="/referral"
        )
        
        # Notify new user about bonus
        await create_notification(
            user_id, "referral",
            f"🎁 Bonus di benvenuto!",
            f"Hai ricevuto {REFERRAL_PUNTI_INVITATO} punti grazie all'invito di {invitante['nome']}!",
            link="/referral"
        )
    
    token = create_token(user_id)
    user_response = UserResponse(
        id=user_id, email=user_data.email, nome=user_data.nome,
        data_registrazione=user_doc["data_registrazione"],
        preferenze=user_doc["preferenze"], statistiche=user_doc["statistiche"],
        referral_code=referral_code, punti_referral=punti_iniziali
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
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
        punti_referral=user.get("punti_referral", 0)
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"], email=current_user["email"], nome=current_user["nome"],
        data_registrazione=current_user["data_registrazione"],
        preferenze=current_user["preferenze"], statistiche=current_user["statistiche"],
        famiglia_id=current_user.get("famiglia_id"),
        referral_code=current_user.get("referral_code"),
        punti_referral=current_user.get("punti_referral", 0)
    )

# ============== REFERRAL PROGRAM ==============

@api_router.get("/referral/stats")
async def get_referral_stats(current_user: dict = Depends(get_current_user)):
    """Ottieni statistiche referral dell'utente"""
    # Get all referrals by this user
    referrals = await db.referrals.find(
        {"invitante_id": current_user["id"]},
        {"_id": 0}
    ).to_list(100)
    
    completati = [r for r in referrals if r["stato"] == "completed"]
    pendenti = [r for r in referrals if r["stato"] == "pending"]
    
    # Calculate bonus history
    storico = []
    for r in completati:
        storico.append({
            "data": r.get("data_completamento"),
            "descrizione": f"Registrazione {r.get('invitato_email', 'utente')}",
            "punti": r.get("punti_assegnati", REFERRAL_PUNTI_INVITANTE)
        })
    
    punti_totali = current_user.get("punti_referral", 0)
    bonus_euro = punti_totali / PUNTI_PER_EURO
    
    return {
        "referral_code": current_user.get("referral_code"),
        "punti_totali": punti_totali,
        "inviti_completati": len(completati),
        "inviti_pendenti": len(pendenti),
        "bonus_disponibile": round(bonus_euro, 2),
        "storico_bonus": storico,
        "punti_per_invito": REFERRAL_PUNTI_INVITANTE,
        "punti_per_registrazione": REFERRAL_PUNTI_INVITATO,
        "punti_per_euro": PUNTI_PER_EURO
    }

@api_router.get("/referral/inviti", response_model=List[ReferralResponse])
async def get_referral_inviti(current_user: dict = Depends(get_current_user)):
    """Ottieni lista inviti referral"""
    inviti = await db.referrals.find(
        {"invitante_id": current_user["id"]},
        {"_id": 0}
    ).sort("data_invito", -1).to_list(50)
    return inviti

@api_router.post("/referral/invita")
async def invita_referral(invito: ReferralInvito, current_user: dict = Depends(get_current_user)):
    """Invia un invito referral via email"""
    # Check if email already registered
    existing_user = await db.utenti.find_one({"email": invito.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Questo utente è già registrato")
    
    # Check if already invited by this user
    existing_invite = await db.referrals.find_one({
        "invitante_id": current_user["id"],
        "invitato_email": invito.email
    })
    if existing_invite:
        raise HTTPException(status_code=400, detail="Hai già invitato questo utente")
    
    # Create referral invite
    referral_doc = {
        "id": str(uuid.uuid4()),
        "invitante_id": current_user["id"],
        "invitante_nome": current_user["nome"],
        "invitato_email": invito.email,
        "invitato_id": None,
        "stato": "pending",
        "punti_assegnati": 0,
        "data_invito": datetime.now(timezone.utc).isoformat(),
        "data_completamento": None
    }
    await db.referrals.insert_one(referral_doc)
    
    return {
        "message": f"Invito inviato a {invito.email}",
        "referral_code": current_user.get("referral_code"),
        "link": f"https://shopply.app/register?ref={current_user.get('referral_code')}"
    }

@api_router.post("/referral/genera-codice")
async def genera_codice_referral(current_user: dict = Depends(get_current_user)):
    """Genera un codice referral per utenti esistenti che non ne hanno uno"""
    if current_user.get("referral_code"):
        return {"referral_code": current_user["referral_code"], "message": "Codice già esistente"}
    
    referral_code = generate_referral_code(current_user["nome"])
    
    # Check if unique
    while await db.utenti.find_one({"referral_code": referral_code}):
        referral_code = generate_referral_code(current_user["nome"])
    
    # Update user
    await db.utenti.update_one(
        {"id": current_user["id"]},
        {"$set": {"referral_code": referral_code, "punti_referral": 0}}
    )
    
    return {"referral_code": referral_code, "message": "Codice generato con successo"}

@api_router.post("/referral/riscatta")
async def riscatta_punti(punti: int, current_user: dict = Depends(get_current_user)):
    """Riscatta punti referral come sconto"""
    if punti <= 0:
        raise HTTPException(status_code=400, detail="Punti non validi")
    
    punti_disponibili = current_user.get("punti_referral", 0)
    if punti > punti_disponibili:
        raise HTTPException(status_code=400, detail="Punti insufficienti")
    
    sconto_euro = punti / PUNTI_PER_EURO
    
    # Update user points
    await db.utenti.update_one(
        {"id": current_user["id"]},
        {"$inc": {"punti_referral": -punti}}
    )
    
    # Create redemption record
    await db.riscatti_referral.insert_one({
        "id": str(uuid.uuid4()),
        "utente_id": current_user["id"],
        "punti_riscattati": punti,
        "valore_euro": sconto_euro,
        "data": datetime.now(timezone.utc).isoformat()
    })
    
    # Notify user
    await create_notification(
        current_user["id"], "referral",
        f"💰 Sconto riscattato!",
        f"Hai riscattato {punti} punti per uno sconto di €{sconto_euro:.2f}",
        link="/referral"
    )
    
    return {
        "message": "Punti riscattati con successo",
        "punti_riscattati": punti,
        "sconto_euro": round(sconto_euro, 2),
        "punti_rimanenti": punti_disponibili - punti
    }

@api_router.get("/referral/classifica")
async def get_classifica_referral():
    """Ottieni classifica top referrer"""
    top_users = await db.utenti.find(
        {"punti_referral": {"$gt": 0}},
        {"_id": 0, "nome": 1, "punti_referral": 1}
    ).sort("punti_referral", -1).limit(10).to_list(10)
    
    classifica = []
    for i, user in enumerate(top_users, 1):
        classifica.append({
            "posizione": i,
            "nome": user["nome"][:2] + "***",  # Privacy
            "punti": user["punti_referral"]
        })
    
    return classifica

# ============== PREFERENZE ==============

@api_router.get("/preferenze", response_model=Preferenze)
async def get_preferenze(current_user: dict = Depends(get_current_user)):
    return Preferenze(**current_user["preferenze"])

@api_router.put("/preferenze", response_model=Preferenze)
async def update_preferenze(prefs: Preferenze, current_user: dict = Depends(get_current_user)):
    await db.utenti.update_one({"id": current_user["id"]}, {"$set": {"preferenze": prefs.model_dump()}})
    return prefs

# ============== SUPERMERCATI ==============

@api_router.get("/supermercati", response_model=List[Supermercato])
async def get_supermercati():
    supermercati = await db.supermercati.find({}, {"_id": 0}).to_list(100)
    return supermercati

@api_router.get("/supermercati/{supermercato_id}", response_model=Supermercato)
async def get_supermercato(supermercato_id: str):
    sup = await db.supermercati.find_one({"id": supermercato_id}, {"_id": 0})
    if not sup:
        raise HTTPException(status_code=404, detail="Supermercato non trovato")
    return sup

# ============== PRODOTTI ==============

@api_router.get("/prodotti", response_model=List[Prodotto])
async def get_prodotti(categoria: Optional[str] = None, search: Optional[str] = None, in_offerta: Optional[bool] = None):
    query = {}
    if categoria:
        query["categoria"] = categoria
    if search:
        query["nome_prodotto"] = {"$regex": search, "$options": "i"}
    if in_offerta:
        query["in_offerta"] = True
    prodotti = await db.prodotti.find(query, {"_id": 0}).to_list(1000)
    return prodotti

@api_router.get("/prodotti/autocomplete")
async def autocomplete_prodotti(q: str):
    if len(q) < 2:
        return []
    prodotti = await db.prodotti.find(
        {"nome_prodotto": {"$regex": f"^{q}", "$options": "i"}},
        {"_id": 0, "nome_prodotto": 1}
    ).to_list(10)
    nomi_unici = list(set([p["nome_prodotto"] for p in prodotti]))
    return nomi_unici[:10]

@api_router.get("/prodotti/offerte")
async def get_offerte():
    """Restituisce prodotti in offerta raggruppati per supermercato"""
    offerte = await db.prodotti.find({"in_offerta": True}, {"_id": 0}).to_list(500)
    
    # Raggruppa per supermercato
    by_store = {}
    for p in offerte:
        store_id = p["supermercato_id"]
        if store_id not in by_store:
            by_store[store_id] = []
        by_store[store_id].append(p)
    
    return by_store

@api_router.get("/categorie")
async def get_categorie():
    categorie = await db.prodotti.distinct("categoria")
    return categorie

# ============== LISTE SPESA ==============

@api_router.get("/liste", response_model=List[ListaSpesa])
async def get_liste(current_user: dict = Depends(get_current_user)):
    # Get own lists and shared lists
    query = {
        "$or": [
            {"utente_id": current_user["id"]},
            {"membri_condivisi": current_user["email"]},
            {"famiglia_id": current_user.get("famiglia_id")} if current_user.get("famiglia_id") else {"_id": None}
        ]
    }
    liste = await db.liste_spesa.find(query, {"_id": 0}).sort("data_creazione", -1).to_list(20)
    return liste

@api_router.post("/liste", response_model=ListaSpesa)
async def create_lista(lista: ListaSpesaCreate, current_user: dict = Depends(get_current_user)):
    count = await db.liste_spesa.count_documents({"utente_id": current_user["id"]})
    if count >= 10:  # Increased limit
        raise HTTPException(status_code=400, detail="Limite di 10 liste raggiunto")
    
    lista_doc = {
        "id": str(uuid.uuid4()),
        "utente_id": current_user["id"],
        "nome": lista.nome,
        "prodotti": lista.prodotti,
        "data_creazione": datetime.now(timezone.utc).isoformat(),
        "condivisa": False,
        "famiglia_id": current_user.get("famiglia_id"),
        "membri_condivisi": []
    }
    await db.liste_spesa.insert_one(lista_doc)
    return ListaSpesa(**lista_doc)

@api_router.put("/liste/{lista_id}")
async def update_lista(lista_id: str, lista: ListaSpesaCreate, current_user: dict = Depends(get_current_user)):
    result = await db.liste_spesa.update_one(
        {"id": lista_id, "$or": [{"utente_id": current_user["id"]}, {"membri_condivisi": current_user["email"]}]},
        {"$set": {"nome": lista.nome, "prodotti": lista.prodotti}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Lista non trovata")
    return {"message": "Lista aggiornata"}

@api_router.delete("/liste/{lista_id}")
async def delete_lista(lista_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.liste_spesa.delete_one({"id": lista_id, "utente_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lista non trovata")
    return {"message": "Lista eliminata"}

# ============== CONDIVISIONE LISTE ==============

@api_router.post("/liste/{lista_id}/condividi")
async def condividi_lista(lista_id: str, req: CondividiListaRequest, current_user: dict = Depends(get_current_user)):
    """Condividi una lista con un altro utente via email"""
    lista = await db.liste_spesa.find_one({"id": lista_id, "utente_id": current_user["id"]}, {"_id": 0})
    if not lista:
        raise HTTPException(status_code=404, detail="Lista non trovata")
    
    # Check if user exists
    destinatario = await db.utenti.find_one({"email": req.email_destinatario}, {"_id": 0})
    
    # Add to shared members
    await db.liste_spesa.update_one(
        {"id": lista_id},
        {"$set": {"condivisa": True}, "$addToSet": {"membri_condivisi": req.email_destinatario}}
    )
    
    # Create notification for recipient if exists
    if destinatario:
        await create_notification(
            destinatario["id"], "condivisione",
            f"📋 Lista condivisa da {current_user['nome']}",
            f"{current_user['nome']} ha condiviso la lista '{lista['nome']}' con te.",
            link=f"/liste/{lista_id}"
        )
    
    return {"message": f"Lista condivisa con {req.email_destinatario}", "success": True}

@api_router.delete("/liste/{lista_id}/condividi/{email}")
async def rimuovi_condivisione(lista_id: str, email: str, current_user: dict = Depends(get_current_user)):
    """Rimuovi condivisione con un utente"""
    result = await db.liste_spesa.update_one(
        {"id": lista_id, "utente_id": current_user["id"]},
        {"$pull": {"membri_condivisi": email}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Lista non trovata")
    return {"message": "Condivisione rimossa"}

# ============== FAMIGLIA ==============

@api_router.post("/famiglia/crea")
async def crea_famiglia(nome: str, current_user: dict = Depends(get_current_user)):
    """Crea un nuovo gruppo famiglia"""
    if current_user.get("famiglia_id"):
        raise HTTPException(status_code=400, detail="Sei già in una famiglia")
    
    famiglia_id = str(uuid.uuid4())
    famiglia_doc = {
        "id": famiglia_id,
        "nome": nome,
        "creatore_id": current_user["id"],
        "membri": [{"id": current_user["id"], "nome": current_user["nome"], "email": current_user["email"], "ruolo": "admin"}],
        "data_creazione": datetime.now(timezone.utc).isoformat()
    }
    await db.famiglie.insert_one(famiglia_doc)
    await db.utenti.update_one({"id": current_user["id"]}, {"$set": {"famiglia_id": famiglia_id}})
    
    return {"message": "Famiglia creata", "famiglia_id": famiglia_id}

@api_router.post("/famiglia/invita")
async def invita_membro(invito: InvitoFamiglia, current_user: dict = Depends(get_current_user)):
    """Invita un membro nella famiglia"""
    if not current_user.get("famiglia_id"):
        raise HTTPException(status_code=400, detail="Non sei in una famiglia")
    
    # Check invitee exists
    invitato = await db.utenti.find_one({"email": invito.email}, {"_id": 0})
    
    # Create invite
    invite_doc = {
        "id": str(uuid.uuid4()),
        "famiglia_id": current_user["famiglia_id"],
        "invitante_id": current_user["id"],
        "invitante_nome": current_user["nome"],
        "email_invitato": invito.email,
        "stato": "pending",
        "data": datetime.now(timezone.utc).isoformat()
    }
    await db.inviti_famiglia.insert_one(invite_doc)
    
    if invitato:
        await create_notification(
            invitato["id"], "condivisione",
            f"👨‍👩‍👧‍👦 Invito famiglia da {current_user['nome']}",
            f"Sei stato invitato a unirti alla famiglia. Vai nelle impostazioni per accettare.",
            link="/impostazioni"
        )
    
    return {"message": f"Invito inviato a {invito.email}"}

@api_router.get("/famiglia/inviti")
async def get_inviti(current_user: dict = Depends(get_current_user)):
    """Ottieni inviti pendenti"""
    inviti = await db.inviti_famiglia.find(
        {"email_invitato": current_user["email"], "stato": "pending"},
        {"_id": 0}
    ).to_list(10)
    return inviti

@api_router.post("/famiglia/inviti/{invito_id}/accetta")
async def accetta_invito(invito_id: str, current_user: dict = Depends(get_current_user)):
    """Accetta un invito famiglia"""
    invito = await db.inviti_famiglia.find_one({"id": invito_id, "email_invitato": current_user["email"]}, {"_id": 0})
    if not invito:
        raise HTTPException(status_code=404, detail="Invito non trovato")
    
    # Join family
    await db.famiglie.update_one(
        {"id": invito["famiglia_id"]},
        {"$push": {"membri": {"id": current_user["id"], "nome": current_user["nome"], "email": current_user["email"], "ruolo": "membro"}}}
    )
    await db.utenti.update_one({"id": current_user["id"]}, {"$set": {"famiglia_id": invito["famiglia_id"]}})
    await db.inviti_famiglia.update_one({"id": invito_id}, {"$set": {"stato": "accepted"}})
    
    return {"message": "Sei entrato nella famiglia!"}

@api_router.get("/famiglia")
async def get_famiglia(current_user: dict = Depends(get_current_user)):
    """Ottieni info famiglia"""
    if not current_user.get("famiglia_id"):
        return None
    famiglia = await db.famiglie.find_one({"id": current_user["famiglia_id"]}, {"_id": 0})
    return famiglia

# ============== NOTIFICHE ==============

async def create_notification(utente_id: str, tipo: str, titolo: str, messaggio: str, link: str = None, dati_extra: dict = None):
    """Helper per creare notifiche"""
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

@api_router.get("/notifiche", response_model=List[Notifica])
async def get_notifiche(current_user: dict = Depends(get_current_user)):
    notifiche = await db.notifiche.find(
        {"utente_id": current_user["id"]},
        {"_id": 0}
    ).sort("data", -1).to_list(50)
    return notifiche

@api_router.get("/notifiche/non-lette")
async def get_notifiche_non_lette(current_user: dict = Depends(get_current_user)):
    count = await db.notifiche.count_documents({"utente_id": current_user["id"], "letta": False})
    return {"count": count}

@api_router.patch("/notifiche/{notifica_id}/letta")
async def segna_letta(notifica_id: str, current_user: dict = Depends(get_current_user)):
    await db.notifiche.update_one(
        {"id": notifica_id, "utente_id": current_user["id"]},
        {"$set": {"letta": True}}
    )
    return {"message": "Notifica segnata come letta"}

@api_router.patch("/notifiche/leggi-tutte")
async def leggi_tutte(current_user: dict = Depends(get_current_user)):
    await db.notifiche.update_many(
        {"utente_id": current_user["id"], "letta": False},
        {"$set": {"letta": True}}
    )
    return {"message": "Tutte le notifiche segnate come lette"}

@api_router.delete("/notifiche/{notifica_id}")
async def elimina_notifica(notifica_id: str, current_user: dict = Depends(get_current_user)):
    await db.notifiche.delete_one({"id": notifica_id, "utente_id": current_user["id"]})
    return {"message": "Notifica eliminata"}

# ============== AGGIORNAMENTO PREZZI AUTOMATICO ==============

@api_router.post("/prezzi/aggiorna")
async def aggiorna_prezzi_manuale(background_tasks: BackgroundTasks):
    """Trigger manuale aggiornamento prezzi (simula scraping)"""
    background_tasks.add_task(aggiorna_prezzi_task)
    return {"message": "Aggiornamento prezzi avviato in background"}

async def aggiorna_prezzi_task():
    """Task per aggiornare i prezzi con variazioni realistiche"""
    prodotti = await db.prodotti.find({}, {"_id": 0}).to_list(10000)
    
    updates = []
    nuove_offerte = []
    
    for prod in prodotti:
        prezzo_attuale = prod["prezzo"]
        prezzo_precedente = prezzo_attuale
        
        # Random price variation (-5% to +3%)
        variazione = random.uniform(-0.05, 0.03)
        nuovo_prezzo = round(prezzo_attuale * (1 + variazione), 2)
        
        # 10% chance of new discount
        in_offerta = random.random() < 0.10
        sconto = None
        if in_offerta:
            sconto = random.choice([10, 15, 20, 25, 30])
            nuovo_prezzo = round(prezzo_attuale * (1 - sconto/100), 2)
            nuove_offerte.append({
                "prodotto": prod["nome_prodotto"],
                "supermercato_id": prod["supermercato_id"],
                "sconto": sconto,
                "prezzo_nuovo": nuovo_prezzo,
                "prezzo_vecchio": prezzo_attuale
            })
        
        updates.append({
            "filter": {"id": prod["id"]},
            "update": {
                "$set": {
                    "prezzo": nuovo_prezzo,
                    "prezzo_precedente": prezzo_precedente,
                    "in_offerta": in_offerta,
                    "sconto_percentuale": sconto,
                    "data_aggiornamento": datetime.now(timezone.utc).isoformat()
                }
            }
        })
    
    # Batch update
    for upd in updates:
        await db.prodotti.update_one(upd["filter"], upd["update"])
    
    # Create notifications for users with offers enabled
    if nuove_offerte:
        users = await db.utenti.find({"preferenze.notifiche_offerte": True}, {"_id": 0, "id": 1}).to_list(1000)
        top_offerte = sorted(nuove_offerte, key=lambda x: x["sconto"], reverse=True)[:5]
        
        for user in users:
            await create_notification(
                user["id"], "offerta",
                f"🔥 {len(nuove_offerte)} nuove offerte disponibili!",
                f"Scopri sconti fino al {top_offerte[0]['sconto']}% su {top_offerte[0]['prodotto']}",
                link="/offerte",
                dati_extra={"offerte_count": len(nuove_offerte)}
            )
    
    # Log update
    await db.aggiornamenti_prezzi.insert_one({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prodotti_aggiornati": len(updates),
        "nuove_offerte": len(nuove_offerte)
    })

@api_router.get("/prezzi/ultimo-aggiornamento")
async def ultimo_aggiornamento():
    """Ottieni info ultimo aggiornamento prezzi"""
    ultimo = await db.aggiornamenti_prezzi.find_one({}, {"_id": 0}, sort=[("timestamp", -1)])
    return ultimo or {"message": "Nessun aggiornamento"}

# ============== OTTIMIZZAZIONE ==============

@api_router.post("/ottimizza", response_model=OttimizzaResponse)
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
    
    prodotti_db = await db.prodotti.find({}, {"_id": 0}).to_list(10000)
    
    prezzi_map = {}
    for prod in prodotti_db:
        nome = prod["nome_prodotto"].lower()
        if nome not in prezzi_map:
            prezzi_map[nome] = {}
        prezzi_map[nome][prod["supermercato_id"]] = {
            "prezzo": prod["prezzo"],
            "in_offerta": prod.get("in_offerta", False)
        }
    
    assegnazioni = {}
    costo_totale = 0.0
    costo_peggiore = 0.0
    
    for prodotto_richiesto in req.lista_prodotti:
        prodotto_lower = prodotto_richiesto.lower()
        if prodotto_lower not in prezzi_map:
            continue
        
        miglior_score = float('inf')
        miglior_sup_id = None
        miglior_prezzo = 0
        miglior_in_offerta = False
        prezzo_max = 0
        
        for sup in supermercati_vicini:
            if sup["id"] not in prezzi_map[prodotto_lower]:
                continue
            
            info_prezzo = prezzi_map[prodotto_lower][sup["id"]]
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
                "prodotto": prodotto_richiesto,
                "prezzo": miglior_prezzo,
                "in_offerta": miglior_in_offerta
            })
            costo_totale += miglior_prezzo
            costo_peggiore += prezzo_max if prezzo_max > 0 else miglior_prezzo
    
    if len(assegnazioni) > req.max_supermercati:
        sorted_sups = sorted(assegnazioni.items(), key=lambda x: len(x[1]), reverse=True)
        assegnazioni = dict(sorted_sups[:req.max_supermercati])
    
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
            ProdottoAssegnato(
                prodotto=p["prodotto"],
                supermercato_id=prossimo_sup_id,
                supermercato_nome=sup_data["nome"],
                prezzo=p["prezzo"],
                in_offerta=p["in_offerta"]
            )
            for p in assegnazioni[prossimo_sup_id]
        ]
        
        subtotale = sum(p["prezzo"] for p in assegnazioni[prossimo_sup_id])
        
        piano.append(SupermercatoPercorso(
            supermercato=Supermercato(**sup_data),
            prodotti=prodotti_assegnati,
            subtotale=subtotale,
            ordine=ordine
        ))
        
        distanza_totale += min_dist
        pos_corrente = (sup_data["lat"], sup_data["lng"])
        sup_rimanenti.remove(prossimo_sup_id)
        ordine += 1
    
    tempo_totale = int(distanza_totale / 30 * 60) + (len(piano) * 10)
    risparmio = max(0, costo_peggiore - costo_totale)
    risparmio_perc = (risparmio / costo_peggiore * 100) if costo_peggiore > 0 else 0
    
    storico_doc = {
        "id": str(uuid.uuid4()),
        "utente_id": current_user["id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_lista": req.lista_prodotti,
        "costo_totale": round(costo_totale, 2),
        "tempo_totale_min": tempo_totale,
        "risparmio": round(risparmio, 2),
        "num_supermercati": len(piano),
        "eseguita": False
    }
    await db.ricerche_storiche.insert_one(storico_doc)
    
    await db.utenti.update_one(
        {"id": current_user["id"]},
        {"$inc": {"statistiche.spese_totali": 1, "statistiche.risparmio_totale_euro": round(risparmio, 2)}}
    )
    
    return OttimizzaResponse(
        piano_ottimale=piano,
        costo_totale=round(costo_totale, 2),
        tempo_stimato_min=tempo_totale,
        risparmio_euro=round(risparmio, 2),
        risparmio_percentuale=round(risparmio_perc, 1),
        num_supermercati=len(piano),
        distanza_totale_km=round(distanza_totale, 2)
    )

# ============== STORICO ==============

@api_router.get("/storico", response_model=List[RicercaStorica])
async def get_storico(current_user: dict = Depends(get_current_user)):
    storico = await db.ricerche_storiche.find(
        {"utente_id": current_user["id"]}, {"_id": 0}
    ).sort("timestamp", -1).to_list(10)
    return storico

@api_router.patch("/storico/{ricerca_id}/eseguita")
async def mark_eseguita(ricerca_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.ricerche_storiche.update_one(
        {"id": ricerca_id, "utente_id": current_user["id"]},
        {"$set": {"eseguita": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ricerca non trovata")
    return {"message": "Ricerca segnata come eseguita"}

# ============== MATRICE PREZZI ==============

@api_router.post("/matrice-prezzi")
async def get_matrice_prezzi(prodotti: List[str]):
    result = {}
    for prodotto in prodotti:
        prezzi_prodotto = await db.prodotti.find(
            {"nome_prodotto": {"$regex": f"^{prodotto}$", "$options": "i"}},
            {"_id": 0, "supermercato_id": 1, "prezzo": 1, "in_offerta": 1, "sconto_percentuale": 1}
        ).to_list(100)
        result[prodotto] = {
            p["supermercato_id"]: {
                "prezzo": p["prezzo"],
                "in_offerta": p.get("in_offerta", False),
                "sconto": p.get("sconto_percentuale")
            } for p in prezzi_prodotto
        }
    return result

# ============== SEED DATABASE ESPANSO ==============

@api_router.post("/seed")
async def seed_database():
    """Popola il database con dati di esempio ESPANSI (~600 prodotti)"""
    
    supermercati_data = [
        {"id": "coop-pioltello", "nome": "Coop Pioltello", "catena": "Coop", "indirizzo": "Via Roma 45, Pioltello MI", "lat": 45.4975, "lng": 9.3306, "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"}, "telefono": "02 9267XXX", "servizi": ["parcheggio", "banco_gastronomia", "panetteria"]},
        {"id": "esselunga-pioltello", "nome": "Esselunga Pioltello", "catena": "Esselunga", "indirizzo": "Via Milano 120, Pioltello MI", "lat": 45.5012, "lng": 9.3245, "orari": {"lun-sab": "07:30-22:00", "dom": "08:00-21:00"}, "telefono": "02 9268XXX", "servizi": ["parcheggio", "banco_gastronomia", "bar", "farmacia"]},
        {"id": "lidl-pioltello", "nome": "Lidl Pioltello", "catena": "Lidl", "indirizzo": "Via Trieste 88, Pioltello MI", "lat": 45.4932, "lng": 9.3189, "orari": {"lun-sab": "08:00-21:30", "dom": "09:00-20:00"}, "telefono": "800 480XXX", "servizi": ["parcheggio", "panetteria"]},
        {"id": "eurospin-pioltello", "nome": "Eurospin Pioltello", "catena": "Eurospin", "indirizzo": "Via Bergamo 56, Pioltello MI", "lat": 45.4889, "lng": 9.3367, "orari": {"lun-sab": "08:30-20:00", "dom": "09:00-13:00"}, "telefono": "02 9269XXX", "servizi": ["parcheggio"]},
        {"id": "carrefour-segrate", "nome": "Carrefour Market Segrate", "catena": "Carrefour", "indirizzo": "Via Kennedy 15, Segrate MI", "lat": 45.4845, "lng": 9.2956, "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"}, "telefono": "02 2135XXX", "servizi": ["parcheggio", "banco_gastronomia", "sushi"]},
        {"id": "penny-pioltello", "nome": "Penny Market Pioltello", "catena": "Penny", "indirizzo": "Via Dante 22, Pioltello MI", "lat": 45.4901, "lng": 9.3298, "orari": {"lun-sab": "08:00-20:30", "dom": "09:00-13:00"}, "telefono": "02 9270XXX", "servizi": ["parcheggio"]},
        {"id": "md-segrate", "nome": "MD Discount Segrate", "catena": "MD", "indirizzo": "Via Verdi 78, Segrate MI", "lat": 45.4867, "lng": 9.3012, "orari": {"lun-sab": "08:00-20:00", "dom": "09:00-13:30"}, "telefono": "02 2140XXX", "servizi": ["parcheggio"]}
    ]
    
    # EXPANDED product categories
    categorie_prodotti = {
        "Latticini": [
            ("Latte Intero 1L", "Granarolo", "1L", 1.49), ("Latte Parzialmente Scremato 1L", "Parmalat", "1L", 1.39),
            ("Latte Scremato 1L", "Zymil", "1L", 1.59), ("Yogurt Bianco", "Müller", "125g", 0.89),
            ("Yogurt Greco", "Fage", "150g", 1.29), ("Yogurt Frutta", "Danone", "125g", 0.79),
            ("Mozzarella", "Galbani", "125g", 1.29), ("Mozzarella di Bufala", "Fattorie Fiandino", "125g", 2.49),
            ("Parmigiano Reggiano", "Parmareggio", "200g", 4.99), ("Grana Padano", "Virgilio", "200g", 3.99),
            ("Pecorino Romano", "Locatelli", "150g", 4.49), ("Burro", "Lurpak", "250g", 2.49),
            ("Burro Italiano", "Granarolo", "250g", 1.99), ("Ricotta", "Santa Lucia", "250g", 1.79),
            ("Mascarpone", "Galbani", "250g", 2.29), ("Stracchino", "Nonno Nanni", "200g", 2.19),
            ("Gorgonzola", "Igor", "150g", 2.99), ("Philadelphia", "Kraft", "150g", 1.99),
            ("Panna da Cucina", "Parmalat", "200ml", 1.09), ("Panna Montata", "Hoplà", "250ml", 1.49),
        ],
        "Pane e Cereali": [
            ("Pane in Cassetta", "Mulino Bianco", "400g", 1.89), ("Pane Integrale", "Mulino Bianco", "400g", 2.19),
            ("Fette Biscottate", "Mulino Bianco", "315g", 1.99), ("Fette Biscottate Integrali", "Mulino Bianco", "315g", 2.29),
            ("Cornflakes", "Kellogg's", "375g", 2.79), ("Corn Flakes Integrali", "Kellogg's", "375g", 3.19),
            ("Muesli", "Vitalis", "600g", 3.49), ("Granola", "Quaker", "500g", 3.99),
            ("Pasta Spaghetti", "Barilla", "500g", 0.99), ("Pasta Penne", "De Cecco", "500g", 1.29),
            ("Pasta Fusilli", "Barilla", "500g", 0.99), ("Pasta Rigatoni", "Rummo", "500g", 1.49),
            ("Pasta Farfalle", "Voiello", "500g", 1.39), ("Pasta Orecchiette", "Divella", "500g", 1.19),
            ("Lasagne", "Barilla", "500g", 2.49), ("Riso Arborio", "Scotti", "1kg", 2.19),
            ("Riso Carnaroli", "Riso Gallo", "1kg", 2.79), ("Riso Basmati", "Scotti", "500g", 1.99),
            ("Farina 00", "Caputo", "1kg", 0.89), ("Farina Manitoba", "Molino Rossetto", "1kg", 1.49),
            ("Semola", "De Cecco", "1kg", 1.19), ("Crackers", "Pavesi", "500g", 1.79),
        ],
        "Frutta e Verdura": [
            ("Mele Golden", "Italia", "1kg", 1.99), ("Mele Fuji", "Italia", "1kg", 2.29),
            ("Pere Conference", "Italia", "1kg", 2.49), ("Banane", "Chiquita", "1kg", 1.49),
            ("Arance", "Sicilia", "1kg", 1.79), ("Limoni", "Sicilia", "500g", 1.29),
            ("Mandarini", "Sicilia", "1kg", 2.19), ("Kiwi", "Zespri", "500g", 2.49),
            ("Fragole", "Italia", "250g", 2.99), ("Uva Bianca", "Italia", "500g", 2.79),
            ("Pomodori", "Italia", "1kg", 2.29), ("Pomodorini Ciliegino", "Sicilia", "500g", 2.49),
            ("Insalata Iceberg", "Italia", "1pz", 0.99), ("Lattuga Romana", "Italia", "1pz", 1.19),
            ("Rucola", "Italia", "100g", 1.49), ("Spinaci", "Italia", "400g", 1.99),
            ("Carote", "Italia", "1kg", 1.29), ("Patate", "Italia", "2kg", 2.49),
            ("Cipolle", "Italia", "1kg", 1.19), ("Aglio", "Italia", "200g", 1.49),
            ("Zucchine", "Italia", "1kg", 2.29), ("Melanzane", "Italia", "1kg", 1.99),
            ("Peperoni", "Italia", "1kg", 2.99), ("Funghi Champignon", "Italia", "400g", 1.99),
            ("Broccoli", "Italia", "500g", 1.79), ("Cavolfiore", "Italia", "1pz", 1.99),
        ],
        "Carne e Pesce": [
            ("Petto di Pollo", "AIA", "500g", 6.99), ("Fusi di Pollo", "AIA", "600g", 4.99),
            ("Cosce di Pollo", "AIA", "1kg", 5.49), ("Macinato Bovino", "Inalca", "400g", 5.49),
            ("Macinato Misto", "Inalca", "400g", 4.99), ("Bistecca di Manzo", "Chianina", "300g", 8.99),
            ("Fettine di Vitello", "Italia", "400g", 7.49), ("Salsiccia", "Aia", "400g", 3.99),
            ("Prosciutto Cotto", "Rovagnati", "100g", 2.49), ("Prosciutto Crudo", "San Daniele", "80g", 3.99),
            ("Mortadella", "Fini", "150g", 2.29), ("Salame Milano", "Citterio", "100g", 2.99),
            ("Bresaola", "Rigamonti", "80g", 3.99), ("Speck", "Senfter", "100g", 3.49),
            ("Salmone Affumicato", "Fjord", "100g", 3.99), ("Tonno in Scatola", "Rio Mare", "160g", 2.79),
            ("Tonno all'Olio", "Nostromo", "160g", 2.49), ("Sgombro in Scatola", "Rio Mare", "125g", 1.99),
            ("Wurstel", "Wudy", "250g", 1.99), ("Cotechino", "Modena", "500g", 4.99),
            ("Filetti di Merluzzo", "Findus", "400g", 5.99), ("Bastoncini di Pesce", "Findus", "450g", 4.49),
        ],
        "Bevande": [
            ("Acqua Naturale 6x1.5L", "Sant'Anna", "9L", 2.49), ("Acqua Frizzante 6x1.5L", "San Pellegrino", "9L", 2.99),
            ("Acqua Effervescente Naturale", "Ferrarelle", "6x1L", 3.49), ("Coca Cola", "Coca-Cola", "1.5L", 1.69),
            ("Coca Cola Zero", "Coca-Cola", "1.5L", 1.69), ("Fanta", "Coca-Cola", "1.5L", 1.59),
            ("Sprite", "Coca-Cola", "1.5L", 1.59), ("Pepsi", "Pepsi", "1.5L", 1.49),
            ("Succo Arancia", "Santal", "1L", 1.49), ("Succo ACE", "Yoga", "1L", 1.39),
            ("Succo Pesca", "Santal", "1L", 1.49), ("Succo Mela", "Zuegg", "1L", 1.59),
            ("Birra Lager", "Peroni", "66cl", 1.29), ("Birra Doppio Malto", "Moretti", "66cl", 1.49),
            ("Birra Artigianale", "Ichnusa", "50cl", 1.99), ("Vino Rosso", "Tavernello", "1L", 2.49),
            ("Vino Bianco", "Tavernello", "1L", 2.49), ("Prosecco", "Mionetto", "75cl", 6.99),
            ("Caffè Macinato", "Lavazza", "250g", 3.99), ("Caffè Capsule", "Nespresso", "10pz", 4.99),
            ("Tè Verde", "Twinings", "25pz", 2.79), ("Tè Nero", "Twinings", "25pz", 2.79),
            ("Camomilla", "Star", "20pz", 1.99),
        ],
        "Snack e Dolci": [
            ("Biscotti Gocciole", "Pavesi", "500g", 2.49), ("Biscotti Macine", "Mulino Bianco", "350g", 1.99),
            ("Biscotti Pan di Stelle", "Mulino Bianco", "350g", 2.49), ("Biscotti Ringo", "Pavesi", "330g", 1.79),
            ("Nutella", "Ferrero", "400g", 3.49), ("Nutella", "Ferrero", "750g", 5.99),
            ("Cioccolato Fondente", "Lindt", "100g", 2.99), ("Cioccolato al Latte", "Milka", "100g", 1.99),
            ("Cioccolatini", "Baci Perugina", "200g", 6.99), ("Patatine", "San Carlo", "150g", 1.99),
            ("Patatine Rustiche", "Amica Chips", "200g", 1.79), ("Taralli", "Fiore", "250g", 1.49),
            ("Grissini", "Mulino Bianco", "280g", 1.29), ("Gelato Vaniglia", "Algida", "500ml", 3.49),
            ("Gelato Cioccolato", "Häagen-Dazs", "460ml", 5.99), ("Merendine Kinder", "Ferrero", "10pz", 3.29),
            ("Merendine Brioche", "Mulino Bianco", "10pz", 2.79), ("Cracker Salati", "Mulino Bianco", "500g", 1.79),
            ("Marmellata Fragole", "Zuegg", "320g", 2.19), ("Marmellata Albicocche", "Zuegg", "320g", 2.19),
            ("Miele", "Ambrosoli", "500g", 4.99), ("Creme Spalmabili", "Novi", "350g", 2.99),
        ],
        "Condimenti e Salse": [
            ("Olio Extravergine", "Monini", "1L", 7.99), ("Olio Extravergine Bio", "Carapelli", "750ml", 9.99),
            ("Olio di Semi", "Cuore", "1L", 2.49), ("Aceto Balsamico", "Ponti", "250ml", 2.99),
            ("Aceto di Vino", "Ponti", "1L", 1.29), ("Sale Fino", "Sale Marino", "1kg", 0.49),
            ("Sale Grosso", "Sale Marino", "1kg", 0.49), ("Pepe Nero", "Cannamela", "50g", 1.99),
            ("Passata di Pomodoro", "Mutti", "700g", 1.49), ("Polpa di Pomodoro", "Cirio", "400g", 0.99),
            ("Pelati", "Mutti", "400g", 1.19), ("Concentrato di Pomodoro", "Mutti", "200g", 1.49),
            ("Pesto Genovese", "Barilla", "190g", 2.49), ("Pesto Rosso", "Barilla", "190g", 2.29),
            ("Maionese", "Calvé", "225ml", 1.99), ("Ketchup", "Heinz", "460g", 2.29),
            ("Senape", "Maille", "200g", 1.99), ("Dado", "Star", "10pz", 1.49),
        ],
        "Surgelati": [
            ("Pizza Margherita", "Buitoni", "350g", 2.99), ("Pizza 4 Formaggi", "Dr.Oetker", "400g", 3.49),
            ("Lasagne Surgelate", "Findus", "600g", 4.99), ("Minestrone", "Findus", "750g", 2.99),
            ("Verdure Miste", "Orogel", "450g", 1.99), ("Piselli", "Bonduelle", "450g", 1.79),
            ("Fagiolini", "Orogel", "450g", 1.89), ("Spinaci Surgelati", "Findus", "450g", 1.99),
            ("Patate Fritte", "McCain", "750g", 2.49), ("Crocchette", "Findus", "400g", 2.79),
            ("Gelato Cono", "Cornetto", "4pz", 3.99), ("Gelato Stecco", "Magnum", "4pz", 4.99),
        ],
        "Igiene e Casa": [
            ("Carta Igienica 8 rotoli", "Scottex", "8pz", 4.99), ("Carta Igienica 12 rotoli", "Tenderly", "12pz", 6.99),
            ("Carta da Cucina", "Scottex", "2pz", 2.49), ("Fazzoletti", "Tempo", "10pz", 1.29),
            ("Detersivo Piatti", "Fairy", "650ml", 2.29), ("Detersivo Piatti Eco", "Svelto", "500ml", 1.99),
            ("Detersivo Lavatrice", "Dash", "25 lavaggi", 7.99), ("Ammorbidente", "Lenor", "650ml", 2.99),
            ("Detersivo Pavimenti", "Mastro Lindo", "1L", 2.49), ("Sgrassatore", "Chanteclair", "625ml", 2.19),
            ("Candeggina", "ACE", "2L", 1.99), ("Spugne", "Vileda", "3pz", 1.49),
            ("Sacchetti Spazzatura", "Domopak", "20pz", 1.99), ("Pellicola", "Domopak", "50m", 2.49),
            ("Alluminio", "Cuki", "20m", 1.99),
        ],
        "Igiene Personale": [
            ("Shampoo", "Pantene", "250ml", 3.49), ("Shampoo Antiforfora", "Head&Shoulders", "250ml", 3.99),
            ("Balsamo", "L'Oréal", "200ml", 3.49), ("Bagnoschiuma", "Dove", "500ml", 2.99),
            ("Sapone Mani", "Dove", "250ml", 2.49), ("Sapone Liquido", "Palmolive", "300ml", 1.99),
            ("Dentifricio", "Colgate", "75ml", 1.99), ("Dentifricio Sbiancante", "Mentadent", "75ml", 2.49),
            ("Spazzolino", "Oral-B", "2pz", 2.99), ("Collutorio", "Listerine", "500ml", 3.99),
            ("Deodorante Spray", "Dove", "150ml", 2.99), ("Deodorante Roll-on", "Nivea", "50ml", 2.49),
            ("Crema Mani", "Neutrogena", "75ml", 3.99), ("Crema Viso", "Nivea", "50ml", 4.99),
            ("Rasoio", "Gillette", "4pz", 9.99), ("Schiuma da Barba", "Gillette", "250ml", 2.99),
        ],
        "Baby e Infanzia": [
            ("Pannolini Taglia 3", "Pampers", "50pz", 14.99), ("Pannolini Taglia 4", "Pampers", "46pz", 12.99),
            ("Pannolini Taglia 5", "Huggies", "42pz", 11.99), ("Salviette Umidificate", "Huggies", "72pz", 2.99),
            ("Latte in Polvere", "Mellin", "800g", 19.99), ("Omogeneizzato Frutta", "Plasmon", "4x100g", 3.49),
            ("Omogeneizzato Carne", "Plasmon", "2x80g", 2.99), ("Biscotti Baby", "Plasmon", "320g", 2.99),
            ("Pastina", "Mellin", "350g", 2.49),
        ],
        "Pet Food": [
            ("Crocchette Cane", "Purina", "3kg", 12.99), ("Crocchette Gatto", "Whiskas", "1.5kg", 7.99),
            ("Scatolette Cane", "Cesar", "4x150g", 4.99), ("Scatolette Gatto", "Sheba", "4x85g", 3.99),
            ("Snack Cane", "Pedigree", "180g", 2.99), ("Lettiera Gatto", "Catsan", "5L", 4.99),
        ]
    }
    
    variazioni = {
        "coop-pioltello": 1.0, "esselunga-pioltello": 1.05, "lidl-pioltello": 0.85,
        "eurospin-pioltello": 0.80, "carrefour-segrate": 0.95, "penny-pioltello": 0.82,
        "md-segrate": 0.78
    }
    
    prodotti_data = []
    for categoria, prodotti in categorie_prodotti.items():
        for nome, brand, formato, prezzo_base in prodotti:
            for sup in supermercati_data:
                variazione = variazioni[sup["id"]]
                prezzo = round(prezzo_base * variazione * random.uniform(0.95, 1.05), 2)
                in_offerta = random.random() < 0.12
                sconto = None
                prezzo_precedente = prezzo
                if in_offerta:
                    sconto = random.choice([10, 15, 20, 25, 30])
                    prezzo = round(prezzo * (1 - sconto/100), 2)
                
                prodotti_data.append({
                    "id": f"{nome.lower().replace(' ', '-')}-{sup['id']}",
                    "nome_prodotto": nome,
                    "categoria": categoria,
                    "brand": brand,
                    "formato": formato,
                    "supermercato_id": sup["id"],
                    "prezzo": prezzo,
                    "prezzo_precedente": prezzo_precedente if in_offerta else None,
                    "in_offerta": in_offerta,
                    "sconto_percentuale": sconto,
                    "data_aggiornamento": datetime.now(timezone.utc).isoformat()
                })
    
    # Clear and insert
    await db.supermercati.delete_many({})
    await db.prodotti.delete_many({})
    await db.supermercati.insert_many(supermercati_data)
    await db.prodotti.insert_many(prodotti_data)
    
    # Create indexes
    await db.prodotti.create_index("nome_prodotto")
    await db.prodotti.create_index("categoria")
    await db.prodotti.create_index("supermercato_id")
    await db.prodotti.create_index("in_offerta")
    
    return {
        "message": "Database popolato con successo",
        "supermercati": len(supermercati_data),
        "prodotti": len(prodotti_data),
        "categorie": len(categorie_prodotti)
    }

# ============== HEALTH ==============

@api_router.get("/")
async def root():
    return {"message": "Shopply API v2.0", "status": "online"}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
