"""
Script de démarrage de l'API backend
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au chemin Python
sys.path.append(str(Path(__file__).resolve().parent))

print("Démarrage de l'API Alezia AI...")

# Initialiser d'abord la base de données
try:
    # Importer en se positionnant dans le dossier backend
    os.chdir(os.path.join(os.path.dirname(__file__), "backend"))
    from backend.utils.db import db_manager

    print(f"Base de données initialisée à {db_manager.db_path}")
except Exception as e:
    print(f"Erreur lors de l'initialisation de la base de données: {e}")
    sys.exit(1)

# Démarrer l'API
try:
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
except Exception as e:
    print(f"Erreur lors du démarrage de l'API: {e}")
    sys.exit(1)
