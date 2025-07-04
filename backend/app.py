"""
Point d'entrée principal de l'API pour le système de JDR avec IA
"""

import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import API_CONFIG, SECURITY_CONFIG
from backend.routes.characters import router as characters_router
from backend.routes.chat import router as chat_router
from backend.routes.memory import router as memory_router
from backend.routes.system import router as system_router
from backend.utils.errors import configure_exception_handlers
from backend.utils.logging_config import configure_http_logging, setup_logging

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
    openapi_url="/openapi.json",
)

# Configuration CORS
cors_origins = SECURITY_CONFIG.get("cors_origins", ["*"])
if not isinstance(cors_origins, list):
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration des gestionnaires d'exceptions
configure_exception_handlers(app)

# Configuration des fichiers statiques
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if frontend_path.exists():
    app.mount(
        "/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets"
    )
    app.mount(
        "/css", StaticFiles(directory=str(frontend_path / "assets" / "css")), name="css"
    )
    app.mount(
        "/js", StaticFiles(directory=str(frontend_path / "assets" / "js")), name="js"
    )

# Inclusion des routes
app.include_router(characters_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(memory_router, prefix="/api")

# Routes de base


@app.get("/")
async def root():
    """Point d'entrée - sert l'interface web principale"""
    return FileResponse(str(frontend_path / "index.html"))


@app.get("/chat.html")
async def chat_page():
    """Page de chat"""
    return FileResponse(str(frontend_path / "chat.html"))


@app.get("/traits-visualizer.html")
async def traits_page():
    """Page de visualisation des traits"""
    return FileResponse(str(frontend_path / "traits-visualizer.html"))


@app.get("/api/")
async def api_root():
    """Point d'entrée de l'API JSON"""
    return {
        "message": "Bienvenue sur l'API Alezia AI",
        "status": "online",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "api": "online",
        "database": "connected",  # À implémenter avec une vérification réelle
    }


# Point d'entrée pour l'exécution directe
if __name__ == "__main__":
    logger.info(f"Démarrage de l'API sur {API_CONFIG['host']}:{API_CONFIG['port']}")
    uvicorn.run(
        "app:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=API_CONFIG["debug"],
        workers=API_CONFIG["workers"],
    )
