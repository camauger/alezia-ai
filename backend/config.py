"""
Configuration pour le systÃ¨me de JDR avec IA non censurÃ©e
OptimisÃ© pour i7-13700HX + RTX 4060 Laptop GPU (8 Go VRAM)
"""

import os
from pathlib import Path

# Chemins de base
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
DB_PATH = DATA_DIR / "jdr_database.sqlite"

# Configuration Ollama
LLM_CONFIG = {
    "model_name": "mistral",  # Modèle par défaut
    "fallback_model": "llama2",  # Modèle de secours
    "max_tokens": 500,  # Nombre maximum de tokens pour les réponses
    "temperature": 0.7,  # Température pour la génération
    "ollama_base_url": "http://localhost:11434",  # URL de base pour Ollama
    "gpu_settings": {
        "gpu_layers": 35,  # Utiliser GPU pour la majoritÃ© des couches
        "num_gpu": 1,
        "batch_size": 512,  # AdaptÃ© Ã  8GB VRAM
        "num_thread": 8     # OptimisÃ© pour i7-13700HX
    }
}

# Configuration de l'API
API_CONFIG = {
    "host": "0.0.0.0",
    "port_range": [8000, 8020],  # Plage de ports à essayer
    "port_file": "api_port.txt",  # Fichier où stocker le port utilisé
    "debug": True,
    "workers": 4,  # Nombre de workers Uvicorn
    "timeout": 120,  # Timeout pour les requÃªtes longues
}

# Configuration des embeddings
EMBEDDING_CONFIG = {
    "model_name": "all-MiniLM-L6-v2",  # ModÃ¨le lÃ©ger mais efficace
    "cache_dir": DATA_DIR / "embeddings",
    "dimensions": 384,  # Dimension des embeddings
    "use_gpu": True,  # Utiliser le GPU pour les embeddings
}

# Limites du systÃ¨me
SYSTEM_LIMITS = {
    "max_context_length": 8192,
    "max_memory_items": 100,
    "max_characters": 20,
    "max_universes": 10,
}

# Configuration de sÃ©curitÃ©
SECURITY_CONFIG = {
    # DurÃ©e de validitÃ© du token (en secondes)
    "token_expiration": 24 * 60 * 60,
    "hash_algorithm": "HS256",
    "cors_origins": ["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5500", "http://127.0.0.1:5500"],
}

# CrÃ©ation des rÃ©pertoires nÃ©cessaires
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EMBEDDING_CONFIG["cache_dir"], exist_ok=True)
