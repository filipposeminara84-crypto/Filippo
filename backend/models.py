"""Shopply - All Pydantic models."""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any


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
    regione: Optional[str] = None
    citta: Optional[str] = None

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
    prodotti_non_trovati: List[str] = []

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

class Notifica(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    utente_id: str
    tipo: str
    titolo: str
    messaggio: str
    data: str
    letta: bool = False
    link: Optional[str] = None
    dati_extra: Optional[Dict[str, Any]] = None

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
    stato: str
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

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
