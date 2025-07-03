"""
Configuration globale de l'application
"""

import os
from pathlib import Path
from typing import Any, Dict

from decouple import Csv, config

# Port du serveur API
API_PORT = config("API_PORT", default=8000, cast=int)

# Configuration des chemins
ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "alezia.db"
MEDIA_DIR = ROOT_DIR / "media"
AVATAR_DIR = MEDIA_DIR / "avatars"

# Créer les répertoires s'ils n'existent pas
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(AVATAR_DIR, exist_ok=True)

# Configuration CORS
CORS_ORIGINS = config("CORS_ORIGINS", default="http://localhost:8080,http://127.0.0.1:8080", cast=Csv())

# Configuration du modèle LLM
LLM_CONFIG = {
    "api_url": config("LLM_API_URL", default="http://localhost:11434/api"),
    "default_model": config("LLM_DEFAULT_MODEL", default="llama3"),
    "mock_mode": config("LLM_MOCK_MODE", default=True, cast=bool),
    "temperature": config("LLM_TEMPERATURE", default=0.7, cast=float),
    "max_tokens": config("LLM_MAX_TOKENS", default=1024, cast=int)
}

# Configuration des embeddings
EMBEDDING_CONFIG = {
    "model_name": config("EMBEDDING_MODEL", default="all-MiniLM-L6-v2"),
    "dimensions": config("EMBEDDING_DIMENSIONS", default=384, cast=int),
    "mock_mode": config("EMBEDDING_MOCK_MODE", default=True, cast=bool),
    "cache_dir": DATA_DIR / "embeddings",
    "use_gpu": config("EMBEDDING_USE_GPU", default=False, cast=bool)
}

# Configuration de la base de données
DB_CONFIG = {
    "db_path": DB_PATH,
    "echo": config("DB_ECHO", default=False, cast=bool)
}

# Configuration de la mémoire
MEMORY_CONFIG = {
    "vector_db_path": DATA_DIR / "vector_db",
    "extraction_threshold": config("EXTRACTION_THRESHOLD", default=0.6, cast=float),
    "similarity_threshold": config("SIMILARITY_THRESHOLD", default=0.7, cast=float),
    "max_relevant_memories": config("MAX_RELEVANT_MEMORIES", default=5, cast=int),
    "check_semantic_similarity": config("CHECK_SEMANTIC_SIMILARITY", default=True, cast=bool)
}

# Configuration du serveur
SERVER_CONFIG = {
    "host": config("HOST", default="0.0.0.0"),
    "port": API_PORT,
    "reload": config("RELOAD", default=True, cast=bool),
    "workers": config("WORKERS", default=1, cast=int),
    "log_level": config("LOG_LEVEL", default="info")
}

# Configuration des logs
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": str(DATA_DIR / "alezia.log"),
            "encoding": "utf8"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True
        }
    }
}

# Écrire le fichier api_port.txt pour le frontend
with open(str(ROOT_DIR / "frontend" / "api_port.txt"), "w") as f:
    f.write(str(API_PORT))


def get_config() -> Dict[str, Any]:
    """
    Récupère la configuration complète

    Returns:
        Dictionnaire de configuration
    """
    return {
        "api_port": API_PORT,
        "root_dir": ROOT_DIR,
        "data_dir": DATA_DIR,
        "db_path": DB_PATH,
        "media_dir": MEDIA_DIR,
        "avatar_dir": AVATAR_DIR,
        "cors_origins": CORS_ORIGINS,
        "llm_config": LLM_CONFIG,
        "embedding_config": EMBEDDING_CONFIG,
        "db_config": DB_CONFIG,
        "memory_config": MEMORY_CONFIG,
        "server_config": SERVER_CONFIG,
        "log_config": LOG_CONFIG
    }
