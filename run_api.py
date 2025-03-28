"""
Script simple pour démarrer l'API
"""

import os
import sys
import socket
from pathlib import Path

# Ajouter le dossier backend au PYTHONPATH
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

# Changer le répertoire courant pour exécuter app.py
os.chdir(str(backend_dir))

# Fonction pour vérifier si un port est disponible


def is_port_available(port):
    """Vérifie si un port est disponible"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except:
            return False

# Trouver un port disponible


def find_available_port(start_port=8000, max_port=8020):
    """Trouve un port disponible dans une plage"""
    for port in range(start_port, max_port + 1):
        if is_port_available(port):
            return port
    return None


# Importer et exécuter l'application
try:
    print("Démarrage de l'API Alezia...")

    import uvicorn
    from app import app

    # Trouver un port disponible
    port = find_available_port()
    if port is None:
        print("ERREUR: Aucun port disponible entre 8000 et 8020. Arrêtez d'autres services ou spécifiez un autre port.")
        sys.exit(1)

    print(f"API sera disponible sur http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
except Exception as e:
    print(f"Erreur lors du démarrage de l'API: {e}")
    sys.exit(1)
