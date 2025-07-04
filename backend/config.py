"""
Configuration for the uncensored AI RPG system
Optimized for i7-13700HX + RTX 4060 Laptop GPU (8 GB VRAM)
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
DB_PATH = DATA_DIR / "jdr_database.sqlite"

# Ollama configuration
LLM_CONFIG = {
    "model_name": "mistral",  # Default model
    "fallback_model": "llama2",  # Fallback model
    "max_tokens": 500,  # Maximum number of tokens for responses
    "temperature": 0.7,  # Temperature for generation
    "ollama_base_url": "http://localhost:11434",  # Base URL for Ollama
    "gpu_settings": {
        "gpu_layers": 35,  # Use GPU for most layers
        "num_gpu": 1,
        "batch_size": 512,  # Adapted to 8GB VRAM
        "num_thread": 8     # Optimized for i7-13700HX
    }
}

# API configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port_range": [8000, 8020],  # Port range to try
    "port_file": "api_port.txt",  # File to store the used port
    "debug": True,
    "workers": 4,  # Number of Uvicorn workers
    "timeout": 120,  # Timeout for long requests
}

# Embeddings configuration
EMBEDDING_CONFIG = {
    "model_name": "all-MiniLM-L6-v2",  # Lightweight but effective model
    "cache_dir": DATA_DIR / "embeddings",
    "dimensions": 384,  # Dimension of the embeddings
    "use_gpu": True,  # Use the GPU for embeddings
}

# System limits
SYSTEM_LIMITS = {
    "max_context_length": 8192,
    "max_memory_items": 100,
    "max_characters": 20,
    "max_universes": 10,
}

# Security configuration
SECURITY_CONFIG = {
    # Token validity duration (in seconds)
    "token_expiration": 24 * 60 * 60,
    "hash_algorithm": "HS256",
    "cors_origins": ["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5500", "http://127.0.0.1:5500"],
}

# Create necessary directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EMBEDDING_CONFIG["cache_dir"], exist_ok=True)
