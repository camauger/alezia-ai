"""
Point d'entrée principal de l'API pour le système de JDR avec IA
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from pathlib import Path
import sys

# Ajout du répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).resolve().parent))

# Import de la configuration
from config import API_CONFIG, SECURITY_CONFIG

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Alezia AI - Système de JDR avec IA non censurée",
    description="API pour interagir avec des personnages IA dans divers univers",
    version="0.1.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=SECURITY_CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    uvicorn.run(
        "app:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=API_CONFIG["debug"],
        workers=API_CONFIG["workers"],
    )