"""
Point d'entrée principal de l'API pour le système de JDR avec IA
"""

from routes.system import router as system_router
from routes.characters import router as characters_router
from routes.chat import router as chat_router
from utils.errors import configure_exception_handlers
from utils.logging_config import setup_logging, configure_http_logging
from config import API_CONFIG, SECURITY_CONFIG
import uvicorn
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

# Ajouter le répertoire parent au chemin Python pour permettre les imports absolus
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import de la configuration

# Import du système de logging

# Import du système de gestion d'erreurs

# Import des routes

# Configuration du logging
logger = setup_logging(log_to_file=True)
configure_http_logging()

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Alezia AI - Système de JDR avec IA non censurée",
    description="API pour interagir avec des personnages IA dans divers univers",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=SECURITY_CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration des gestionnaires d'exceptions
configure_exception_handlers(app)

# Inclusion des routes
app.include_router(characters_router)
app.include_router(system_router)
app.include_router(chat_router)

# Routes de base


@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "Bienvenue sur l'API Alezia AI",
        "status": "online",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "api": "online",
        "database": "connected"  # À implémenter avec une vérification réelle
    }

# Point d'entrée pour l'exécution directe
if __name__ == "__main__":
    logger.info(
        f"Démarrage de l'API sur {API_CONFIG['host']}:{API_CONFIG['port']}")
    uvicorn.run(
        "app:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=API_CONFIG["debug"],
        workers=API_CONFIG["workers"],
    )
