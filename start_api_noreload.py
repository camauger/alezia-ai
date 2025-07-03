"""
Script simplifié pour démarrer l'API Alezia AI sans rechargement automatique
"""

import sys
from pathlib import Path

import uvicorn

# Configuration
PORT = 8006  # Utiliser un port différent pour éviter les conflits
HOST = "0.0.0.0"

# Ajouter le répertoire courant au chemin Python
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

print(f"Démarrage de l'API Alezia AI sur le port {PORT}...")
print(f"Répertoire courant: {current_dir}")
print(f"Python path: {sys.path}")

# Enregistrer le port dans un fichier pour que le frontend puisse le lire
try:
    with open("api_port.txt", "w") as f:
        f.write(str(PORT))
    print(f"Port {PORT} enregistré dans api_port.txt")
except Exception as e:
    print(f"Erreur lors de l'enregistrement du port: {e}")

# Démarrer l'API
try:
    # Démarrer l'application directement depuis backend/app.py
    uvicorn.run(
        "backend.app:app",
        host=HOST,
        port=PORT,
        reload=False,  # Désactiver le rechargement pour éviter les problèmes
        log_level="info"
    )
except Exception as e:
    print(f"Erreur lors du démarrage de l'API: {e}")
    sys.exit(1)
