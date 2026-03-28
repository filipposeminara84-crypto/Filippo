"""Shopply API - Main application entry point."""
import os
import logging
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from database import client
from routes.auth import router as auth_router
from routes.referral import router as referral_router
from routes.supermercati import router as supermercati_router
from routes.liste import router as liste_router
from routes.famiglia import router as famiglia_router
from routes.notifiche import router as notifiche_router
from routes.ottimizza import router as ottimizza_router
from routes.scraper_routes import router as scraper_router
from routes.seed import router as seed_router
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Shopply API", version="2.7.0")
api_router = APIRouter(prefix="/api")

# Include all route modules
api_router.include_router(auth_router)
api_router.include_router(referral_router)
api_router.include_router(supermercati_router)
api_router.include_router(liste_router)
api_router.include_router(famiglia_router)
api_router.include_router(notifiche_router)
api_router.include_router(ottimizza_router)
api_router.include_router(scraper_router)
api_router.include_router(seed_router)


@api_router.get("/")
async def root():
    return {"message": "Shopply API v2.7.0", "status": "online"}


@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
