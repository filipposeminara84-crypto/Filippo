from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
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

app = FastAPI(title="Shopply API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# ============== MODELS ==============

class UserBase(BaseModel):
    email: EmailStr
    nome: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    data_registrazione: str
    preferenze: Dict[str, Any]
    statistiche: Dict[str, Any]

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
    prezzo_unitario: Optional[float] = None
    in_offerta: bool = False
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
    """Calcola distanza in km tra due punti"""
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def stima_tempo_percorso(distanza_km: float) -> int:
    """Stima tempo in minuti (media 30km/h in città + 5min per negozio)"""
    return int(distanza_km / 30 * 60) + 5

# ============== AUTH ENDPOINTS ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.utenti.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    user_id = str(uuid.uuid4())
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
            "supermercati_preferiti": []
        },
        "statistiche": {
            "spese_totali": 0,
            "risparmio_totale_euro": 0.0,
            "tempo_totale_risparmiato_min": 0
        }
    }
    await db.utenti.insert_one(user_doc)
    
    token = create_token(user_id)
    user_response = UserResponse(
        id=user_id,
        email=user_data.email,
        nome=user_data.nome,
        data_registrazione=user_doc["data_registrazione"],
        preferenze=user_doc["preferenze"],
        statistiche=user_doc["statistiche"]
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    user = await db.utenti.find_one({"email": login_data.email}, {"_id": 0})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    
    token = create_token(user["id"])
    user_response = UserResponse(
        id=user["id"],
        email=user["email"],
        nome=user["nome"],
        data_registrazione=user["data_registrazione"],
        preferenze=user["preferenze"],
        statistiche=user["statistiche"]
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ============== PREFERENZE ==============

@api_router.get("/preferenze", response_model=Preferenze)
async def get_preferenze(current_user: dict = Depends(get_current_user)):
    return Preferenze(**current_user["preferenze"])

@api_router.put("/preferenze", response_model=Preferenze)
async def update_preferenze(prefs: Preferenze, current_user: dict = Depends(get_current_user)):
    await db.utenti.update_one(
        {"id": current_user["id"]},
        {"$set": {"preferenze": prefs.model_dump()}}
    )
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
async def get_prodotti(categoria: Optional[str] = None, search: Optional[str] = None):
    query = {}
    if categoria:
        query["categoria"] = categoria
    if search:
        query["nome_prodotto"] = {"$regex": search, "$options": "i"}
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

@api_router.get("/categorie")
async def get_categorie():
    categorie = await db.prodotti.distinct("categoria")
    return categorie

# ============== LISTE SPESA ==============

@api_router.get("/liste", response_model=List[ListaSpesa])
async def get_liste(current_user: dict = Depends(get_current_user)):
    liste = await db.liste_spesa.find(
        {"utente_id": current_user["id"]},
        {"_id": 0}
    ).sort("data_creazione", -1).to_list(5)
    return liste

@api_router.post("/liste", response_model=ListaSpesa)
async def create_lista(lista: ListaSpesaCreate, current_user: dict = Depends(get_current_user)):
    count = await db.liste_spesa.count_documents({"utente_id": current_user["id"]})
    if count >= 5:
        raise HTTPException(status_code=400, detail="Limite di 5 liste raggiunto")
    
    lista_doc = {
        "id": str(uuid.uuid4()),
        "utente_id": current_user["id"],
        "nome": lista.nome,
        "prodotti": lista.prodotti,
        "data_creazione": datetime.now(timezone.utc).isoformat()
    }
    await db.liste_spesa.insert_one(lista_doc)
    return ListaSpesa(**lista_doc)

@api_router.delete("/liste/{lista_id}")
async def delete_lista(lista_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.liste_spesa.delete_one({"id": lista_id, "utente_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lista non trovata")
    return {"message": "Lista eliminata"}

# ============== OTTIMIZZAZIONE ==============

@api_router.post("/ottimizza", response_model=OttimizzaResponse)
async def ottimizza_spesa(req: OttimizzaRequest, current_user: dict = Depends(get_current_user)):
    # 1. Trova supermercati nel raggio
    supermercati = await db.supermercati.find({}, {"_id": 0}).to_list(100)
    supermercati_vicini = []
    
    for sup in supermercati:
        dist = haversine_distance(req.lat_utente, req.lng_utente, sup["lat"], sup["lng"])
        if dist <= req.raggio_km:
            sup["distanza"] = dist
            supermercati_vicini.append(sup)
    
    if not supermercati_vicini:
        raise HTTPException(status_code=400, detail="Nessun supermercato trovato nel raggio specificato")
    
    # 2. Trova prezzi per ogni prodotto in ogni supermercato
    prodotti_db = await db.prodotti.find({}, {"_id": 0}).to_list(5000)
    
    # Mappa: prodotto_nome -> {supermercato_id: {prezzo, supermercato_nome}}
    prezzi_map = {}
    for prod in prodotti_db:
        nome = prod["nome_prodotto"].lower()
        if nome not in prezzi_map:
            prezzi_map[nome] = {}
        prezzi_map[nome][prod["supermercato_id"]] = {
            "prezzo": prod["prezzo"],
            "in_offerta": prod.get("in_offerta", False)
        }
    
    # 3. Algoritmo Greedy ottimizzato
    # Per ogni prodotto, trova il miglior supermercato considerando prezzo e distanza
    assegnazioni = {}  # supermercato_id -> lista prodotti
    costo_totale = 0.0
    costo_peggiore = 0.0
    
    for prodotto_richiesto in req.lista_prodotti:
        prodotto_lower = prodotto_richiesto.lower()
        if prodotto_lower not in prezzi_map:
            continue
        
        miglior_score = float('inf')
        miglior_sup_id = None
        miglior_prezzo = 0
        prezzo_max = 0
        
        for sup in supermercati_vicini:
            if sup["id"] not in prezzi_map[prodotto_lower]:
                continue
            
            info_prezzo = prezzi_map[prodotto_lower][sup["id"]]
            prezzo = info_prezzo["prezzo"]
            distanza = sup["distanza"]
            
            # Score combinato (normalizzato)
            score = (req.peso_prezzo * prezzo / 10) + (req.peso_tempo * distanza / req.raggio_km)
            
            if score < miglior_score:
                miglior_score = score
                miglior_sup_id = sup["id"]
                miglior_prezzo = prezzo
            
            if prezzo > prezzo_max:
                prezzo_max = prezzo
        
        if miglior_sup_id:
            if miglior_sup_id not in assegnazioni:
                assegnazioni[miglior_sup_id] = []
            assegnazioni[miglior_sup_id].append({
                "prodotto": prodotto_richiesto,
                "prezzo": miglior_prezzo
            })
            costo_totale += miglior_prezzo
            costo_peggiore += prezzo_max if prezzo_max > 0 else miglior_prezzo
    
    # 4. Limita al numero massimo di supermercati
    if len(assegnazioni) > req.max_supermercati:
        # Ordina per numero prodotti (priorità) e redistribuisci
        sorted_sups = sorted(assegnazioni.items(), key=lambda x: len(x[1]), reverse=True)
        assegnazioni = dict(sorted_sups[:req.max_supermercati])
    
    # 5. Calcola percorso ottimale (nearest neighbor)
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
                prezzo=p["prezzo"]
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
    
    # Tempo stimato
    tempo_totale = int(distanza_totale / 30 * 60) + (len(piano) * 10)  # 10 min per negozio
    
    # Risparmio
    risparmio = max(0, costo_peggiore - costo_totale)
    risparmio_perc = (risparmio / costo_peggiore * 100) if costo_peggiore > 0 else 0
    
    # Salva nello storico
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
    
    # Aggiorna statistiche utente
    await db.utenti.update_one(
        {"id": current_user["id"]},
        {"$inc": {
            "statistiche.spese_totali": 1,
            "statistiche.risparmio_totale_euro": round(risparmio, 2)
        }}
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
        {"utente_id": current_user["id"]},
        {"_id": 0}
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
    """Restituisce matrice prezzi: prodotto -> supermercato -> prezzo"""
    result = {}
    for prodotto in prodotti:
        prezzi_prodotto = await db.prodotti.find(
            {"nome_prodotto": {"$regex": f"^{prodotto}$", "$options": "i"}},
            {"_id": 0, "supermercato_id": 1, "prezzo": 1, "in_offerta": 1}
        ).to_list(100)
        result[prodotto] = {p["supermercato_id"]: {"prezzo": p["prezzo"], "in_offerta": p.get("in_offerta", False)} for p in prezzi_prodotto}
    return result

# ============== SEED DATA ==============

@api_router.post("/seed")
async def seed_database():
    """Popola il database con dati di esempio"""
    
    # Supermercati area Pioltello (coordinate reali)
    supermercati_data = [
        {
            "id": "coop-pioltello",
            "nome": "Coop Pioltello",
            "catena": "Coop",
            "indirizzo": "Via Roma 45, Pioltello MI",
            "lat": 45.4975,
            "lng": 9.3306,
            "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"},
            "telefono": "02 9267XXX",
            "servizi": ["parcheggio", "banco_gastronomia", "panetteria"]
        },
        {
            "id": "esselunga-pioltello",
            "nome": "Esselunga Pioltello",
            "catena": "Esselunga",
            "indirizzo": "Via Milano 120, Pioltello MI",
            "lat": 45.5012,
            "lng": 9.3245,
            "orari": {"lun-sab": "07:30-22:00", "dom": "08:00-21:00"},
            "telefono": "02 9268XXX",
            "servizi": ["parcheggio", "banco_gastronomia", "bar", "farmacia"]
        },
        {
            "id": "lidl-pioltello",
            "nome": "Lidl Pioltello",
            "catena": "Lidl",
            "indirizzo": "Via Trieste 88, Pioltello MI",
            "lat": 45.4932,
            "lng": 9.3189,
            "orari": {"lun-sab": "08:00-21:30", "dom": "09:00-20:00"},
            "telefono": "800 480XXX",
            "servizi": ["parcheggio", "panetteria"]
        },
        {
            "id": "eurospin-pioltello",
            "nome": "Eurospin Pioltello",
            "catena": "Eurospin",
            "indirizzo": "Via Bergamo 56, Pioltello MI",
            "lat": 45.4889,
            "lng": 9.3367,
            "orari": {"lun-sab": "08:30-20:00", "dom": "09:00-13:00"},
            "telefono": "02 9269XXX",
            "servizi": ["parcheggio"]
        },
        {
            "id": "carrefour-segrate",
            "nome": "Carrefour Market Segrate",
            "catena": "Carrefour",
            "indirizzo": "Via Kennedy 15, Segrate MI",
            "lat": 45.4845,
            "lng": 9.2956,
            "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"},
            "telefono": "02 2135XXX",
            "servizi": ["parcheggio", "banco_gastronomia", "sushi"]
        }
    ]
    
    # Prodotti comuni con prezzi variabili
    categorie_prodotti = {
        "Latticini": [
            ("Latte Intero 1L", "Granarolo", "1L"),
            ("Latte Parzialmente Scremato 1L", "Parmalat", "1L"),
            ("Yogurt Bianco", "Müller", "125g"),
            ("Mozzarella", "Galbani", "125g"),
            ("Parmigiano Reggiano", "Parmareggio", "200g"),
            ("Burro", "Lurpak", "250g"),
            ("Ricotta", "Santa Lucia", "250g"),
            ("Mascarpone", "Galbani", "250g"),
        ],
        "Pane e Cereali": [
            ("Pane in Cassetta", "Mulino Bianco", "400g"),
            ("Fette Biscottate", "Mulino Bianco", "315g"),
            ("Cornflakes", "Kellogg's", "375g"),
            ("Muesli", "Vitalis", "600g"),
            ("Pasta Spaghetti", "Barilla", "500g"),
            ("Pasta Penne", "De Cecco", "500g"),
            ("Riso Arborio", "Scotti", "1kg"),
            ("Farina 00", "Caputo", "1kg"),
        ],
        "Frutta e Verdura": [
            ("Mele Golden", "Italia", "1kg"),
            ("Banane", "Chiquita", "1kg"),
            ("Arance", "Sicilia", "1kg"),
            ("Pomodori", "Italia", "1kg"),
            ("Insalata Iceberg", "Italia", "1pz"),
            ("Carote", "Italia", "1kg"),
            ("Patate", "Italia", "2kg"),
            ("Cipolle", "Italia", "1kg"),
        ],
        "Carne e Pesce": [
            ("Petto di Pollo", "AIA", "500g"),
            ("Macinato Bovino", "Inalca", "400g"),
            ("Prosciutto Cotto", "Rovagnati", "100g"),
            ("Salmone Affumicato", "Fjord", "100g"),
            ("Tonno in Scatola", "Rio Mare", "160g"),
            ("Wurstel", "Wudy", "250g"),
            ("Bresaola", "Rigamonti", "80g"),
            ("Mortadella", "Fini", "150g"),
        ],
        "Bevande": [
            ("Acqua Naturale 6x1.5L", "Sant'Anna", "9L"),
            ("Acqua Frizzante 6x1.5L", "San Pellegrino", "9L"),
            ("Coca Cola", "Coca-Cola", "1.5L"),
            ("Succo Arancia", "Santal", "1L"),
            ("Birra Lager", "Peroni", "66cl"),
            ("Vino Rosso", "Tavernello", "1L"),
            ("Caffè Macinato", "Lavazza", "250g"),
            ("Tè Verde", "Twinings", "25pz"),
        ],
        "Snack e Dolci": [
            ("Biscotti Gocciole", "Pavesi", "500g"),
            ("Nutella", "Ferrero", "400g"),
            ("Cioccolato Fondente", "Lindt", "100g"),
            ("Patatine", "San Carlo", "150g"),
            ("Gelato Vaniglia", "Algida", "500ml"),
            ("Merendine Kinder", "Ferrero", "10pz"),
            ("Cracker Salati", "Mulino Bianco", "500g"),
            ("Marmellata Fragole", "Zuegg", "320g"),
        ],
        "Igiene e Casa": [
            ("Carta Igienica 8 rotoli", "Scottex", "8pz"),
            ("Detersivo Piatti", "Fairy", "650ml"),
            ("Detersivo Lavatrice", "Dash", "25 lavaggi"),
            ("Shampoo", "Pantene", "250ml"),
            ("Dentifricio", "Colgate", "75ml"),
            ("Sapone Mani", "Dove", "250ml"),
            ("Pannolini Taglia 4", "Pampers", "46pz"),
            ("Salviette Umidificate", "Huggies", "72pz"),
        ]
    }
    
    # Genera prezzi per ogni supermercato (con variazioni realistiche)
    import random
    
    base_prezzi = {
        "Latte Intero 1L": 1.49, "Latte Parzialmente Scremato 1L": 1.39, "Yogurt Bianco": 0.89,
        "Mozzarella": 1.29, "Parmigiano Reggiano": 4.99, "Burro": 2.49, "Ricotta": 1.79, "Mascarpone": 2.29,
        "Pane in Cassetta": 1.89, "Fette Biscottate": 1.99, "Cornflakes": 2.79, "Muesli": 3.49,
        "Pasta Spaghetti": 0.99, "Pasta Penne": 1.29, "Riso Arborio": 2.19, "Farina 00": 0.89,
        "Mele Golden": 1.99, "Banane": 1.49, "Arance": 1.79, "Pomodori": 2.29,
        "Insalata Iceberg": 0.99, "Carote": 1.29, "Patate": 2.49, "Cipolle": 1.19,
        "Petto di Pollo": 6.99, "Macinato Bovino": 5.49, "Prosciutto Cotto": 2.49, "Salmone Affumicato": 3.99,
        "Tonno in Scatola": 2.79, "Wurstel": 1.99, "Bresaola": 3.99, "Mortadella": 2.29,
        "Acqua Naturale 6x1.5L": 2.49, "Acqua Frizzante 6x1.5L": 2.99, "Coca Cola": 1.69, "Succo Arancia": 1.49,
        "Birra Lager": 1.29, "Vino Rosso": 2.49, "Caffè Macinato": 3.99, "Tè Verde": 2.79,
        "Biscotti Gocciole": 2.49, "Nutella": 3.49, "Cioccolato Fondente": 2.99, "Patatine": 1.99,
        "Gelato Vaniglia": 3.49, "Merendine Kinder": 3.29, "Cracker Salati": 1.79, "Marmellata Fragole": 2.19,
        "Carta Igienica 8 rotoli": 4.99, "Detersivo Piatti": 2.29, "Detersivo Lavatrice": 7.99, "Shampoo": 3.49,
        "Dentifricio": 1.99, "Sapone Mani": 2.49, "Pannolini Taglia 4": 12.99, "Salviette Umidificate": 2.99
    }
    
    # Variazioni prezzo per catena
    variazioni = {
        "coop-pioltello": 1.0,
        "esselunga-pioltello": 1.05,
        "lidl-pioltello": 0.85,
        "eurospin-pioltello": 0.80,
        "carrefour-segrate": 0.95
    }
    
    prodotti_data = []
    for categoria, prodotti in categorie_prodotti.items():
        for nome, brand, formato in prodotti:
            for sup in supermercati_data:
                variazione = variazioni[sup["id"]]
                prezzo_base = base_prezzi.get(nome, 2.99)
                prezzo = round(prezzo_base * variazione * random.uniform(0.95, 1.05), 2)
                in_offerta = random.random() < 0.15  # 15% prodotti in offerta
                if in_offerta:
                    prezzo = round(prezzo * 0.8, 2)  # 20% sconto
                
                prodotti_data.append({
                    "id": f"{nome.lower().replace(' ', '-')}-{sup['id']}",
                    "nome_prodotto": nome,
                    "categoria": categoria,
                    "brand": brand,
                    "formato": formato,
                    "supermercato_id": sup["id"],
                    "prezzo": prezzo,
                    "in_offerta": in_offerta,
                    "data_aggiornamento": datetime.now(timezone.utc).isoformat()
                })
    
    # Inserisci dati
    await db.supermercati.delete_many({})
    await db.prodotti.delete_many({})
    
    await db.supermercati.insert_many(supermercati_data)
    await db.prodotti.insert_many(prodotti_data)
    
    return {
        "message": "Database popolato con successo",
        "supermercati": len(supermercati_data),
        "prodotti": len(prodotti_data)
    }

# ============== HEALTH ==============

@api_router.get("/")
async def root():
    return {"message": "Shopply API v1.0", "status": "online"}

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
