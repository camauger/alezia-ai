"""
Configuration globale de l'application
"""

import os
import json
from typing import Dict, Any

# Port du serveur API
API_PORT = int(os.environ.get("API_PORT", 8000))

# Configuration des chemins
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "alezia.db")
MEDIA_DIR = os.path.join(ROOT_DIR, "media")
AVATAR_DIR = os.path.join(MEDIA_DIR, "avatars")

# Créer les répertoires s'ils n'existent pas
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(AVATAR_DIR, exist_ok=True)

# Configuration CORS
CORS_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Configuration du modèle LLM
LLM_CONFIG = {
    "api_url": os.environ.get("LLM_API_URL", "http://localhost:11434/api"),
    "default_model": os.environ.get("LLM_DEFAULT_MODEL", "llama3"),
    "mock_mode": os.environ.get("LLM_MOCK_MODE", "True").lower() in ("true", "1", "t"),
    "temperature": float(os.environ.get("LLM_TEMPERATURE", "0.7")),
    "max_tokens": int(os.environ.get("LLM_MAX_TOKENS", "1024"))
}

# Configuration de la base de données
DB_CONFIG = {
    "db_path": DB_PATH,
    "echo": os.environ.get("DB_ECHO", "False").lower() in ("true", "1", "t")
}

# Configuration de la mémoire
MEMORY_CONFIG = {
    "vector_db_path": os.path.join(DATA_DIR, "vector_db"),
    "extraction_threshold": float(os.environ.get("EXTRACTION_THRESHOLD", "0.6")),
    "similarity_threshold": float(os.environ.get("SIMILARITY_THRESHOLD", "0.7")),
    "max_relevant_memories": int(os.environ.get("MAX_RELEVANT_MEMORIES", "5")),
    "check_semantic_similarity": os.environ.get("CHECK_SEMANTIC_SIMILARITY", "True").lower() in ("true", "1", "t")
}

# Configuration du serveur
SERVER_CONFIG = {
    "host": os.environ.get("HOST", "0.0.0.0"),
    "port": API_PORT,
    "reload": os.environ.get("RELOAD", "True").lower() in ("true", "1", "t"),
    "workers": int(os.environ.get("WORKERS", "1")),
    "log_level": os.environ.get("LOG_LEVEL", "info")
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
            "filename": os.path.join(DATA_DIR, "alezia.log"),
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
with open(os.path.join(ROOT_DIR, "frontend", "api_port.txt"), "w") as f:
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
        "db_config": DB_CONFIG,
        "memory_config": MEMORY_CONFIG,
        "server_config": SERVER_CONFIG,
        "log_config": LOG_CONFIG
    }
