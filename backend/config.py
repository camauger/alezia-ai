"""
Configuration for the uncensored AI RPG system
Optimized for i7-13700HX + RTX 4060 Laptop GPU (8 GB VRAM)
"""

import os
from pathlib import Path

from decouple import Csv, config

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / 'data'
DB_PATH = DATA_DIR / 'alezia.db'

# Ollama configuration (clés lues par backend/services/llm_service.py)
LLM_CONFIG = {
    'api_url': config('LLM_API_URL', default='http://localhost:11434/api'),
    'default_model': config('LLM_DEFAULT_MODEL', default='llama3'),
    'mock_mode': config('LLM_MOCK_MODE', default=False, cast=bool),
    'temperature': config('LLM_TEMPERATURE', default=0.7, cast=float),
    'max_tokens': config('LLM_MAX_TOKENS', default=1024, cast=int),
}

# API configuration
API_CONFIG = {
    'host': '0.0.0.0',
    'port_range': [8000, 8020],  # Port range to try
    'port_file': 'api_port.txt',  # File to store the used port
    'debug': True,
    'workers': 4,  # Number of Uvicorn workers
    'timeout': 120,  # Timeout for long requests
}

# Embeddings configuration
EMBEDDING_CONFIG = {
    'model_name': config('EMBEDDING_MODEL', default='all-MiniLM-L6-v2'),
    'cache_dir': DATA_DIR / 'embeddings',
    'dimensions': config('EMBEDDING_DIMENSIONS', default=384, cast=int),
    'use_gpu': config('EMBEDDING_USE_GPU', default=False, cast=bool),
    'mock_mode': config('EMBEDDING_MOCK_MODE', default=True, cast=bool),
}

# System limits
SYSTEM_LIMITS = {
    'max_context_length': 8192,
    'max_memory_items': 100,
    'max_characters': 20,
    'max_universes': 10,
}

# Security configuration
SECURITY_CONFIG = {
    # Token validity duration (in seconds)
    'token_expiration': config('TOKEN_EXPIRATION', default=24 * 60 * 60, cast=int),
    'hash_algorithm': config('HASH_ALGORITHM', default='HS256'),
    'cors_origins': config(
        'CORS_ORIGINS',
        default='http://localhost:8080,http://127.0.0.1:8080,http://localhost:5500,http://127.0.0.1:5500',
        cast=Csv(),
    ),
}

# Create necessary directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EMBEDDING_CONFIG['cache_dir'], exist_ok=True)
