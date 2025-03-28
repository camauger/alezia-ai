"""
Configuration pour le système de JDR avec IA non censurée
Optimisé pour i7-13700HX + RTX 4060 Laptop GPU (8 Go VRAM)
"""

import os
from pathlib import Path

# Chemins de base
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
DB_PATH = DATA_DIR / "jdr_database.sqlite"

# Configuration Ollama
LLM_CONFIG = {
    "api_host": "http://localhost:11434",
    "default_model": "roleplay-uncensored",
    "fallback_model": "llama3:8b-instruct-uncensored",  # Modèle plus léger en fallback
    "gpu_settings": {
        "gpu_layers": 35,  # Utiliser GPU pour la majorité des couches
        "num_gpu": 1,
        "batch_size": 512,  # Adapté à 8GB VRAM
        "num_thread": 8     # Optimisé pour i7-13700HX
    }
}

# Configuration de l'API
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": True,
    "workers": 4,  # Nombre de workers Uvicorn
    "timeout": 120,  # Timeout pour les requêtes longues
}

# Configuration des embeddings
EMBEDDING_CONFIG = {
    "model_name": "all-MiniLM-L6-v2",  # Modèle léger mais efficace
    "cache_dir": DATA_DIR / "embeddings",
    "dimensions": 384,  # Dimension des embeddings
    "use_gpu": True,  # Utiliser le GPU pour les embeddings
}

# Limites du système
SYSTEM_LIMITS = {
    "max_context_length": 8192,
    "max_memory_items": 100,
    "max_characters": 20,
    "max_universes": 10,
}

# Configuration de sécurité
SECURITY_CONFIG = {
    "token_expiration": 24 * 60 * 60,  # Durée de validité du token (en secondes)
    "hash_algorithm": "HS256",
    "cors_origins": ["http://localhost:8080", "http://127.0.0.1:8080"],
}

# Création des répertoires nécessaires
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EMBEDDING_CONFIG["cache_dir"], exist_ok=True)