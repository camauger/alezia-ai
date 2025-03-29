"""
Script simple pour démarrer l'API
"""

import os
import sys
import socket
from pathlib import Path
import argparse
import signal
import logging

# Ajouter le dossier backend au PYTHONPATH
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

# Changer le répertoire courant pour exécuter app.py
os.chdir(str(backend_dir))

# Constantes
LISTEN_HOST = "0.0.0.0"  # Écoute sur toutes les interfaces

# Fonction pour vérifier si un port est disponible


def is_port_available(port):
    """Vérifie si un port est disponible"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((LISTEN_HOST, port))
            return True
        except socket.error as e:
            return False

# Trouver un port disponible


def find_available_port(start_port=8000, max_port=8020):
    """Trouve un port disponible dans une plage"""
    for port in range(start_port, max_port + 1):
        if is_port_available(port):
            print(f"Port {port} disponible")
            return port
        else:
            print(f"Port {port} déjà utilisé")
    return None


def handle_exit(sig, frame):
    print("\nArrêt propre de l'API...")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# Importer et exécuter l'application
try:
    if not backend_dir.exists():
        print(f"ERREUR: Dossier backend introuvable à {backend_dir}")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info("Démarrage de l'API Alezia...")

    try:
        import uvicorn
    except ImportError:
        print("ERREUR: uvicorn n'est pas installé. Exécutez 'pip install uvicorn'.")
        sys.exit(1)

    from app import app

    parser = argparse.ArgumentParser(description="Démarrage de l'API Alezia")
    parser.add_argument(
        "--port", type=int, help="Port à utiliser (laissez vide pour auto-détection)")
    args = parser.parse_args()

    # Trouver un port disponible
    port = args.port if args.port else find_available_port()
    if port is None:
        print("ERREUR: Aucun port disponible entre 8000 et 8020. Arrêtez d'autres services ou spécifiez un autre port.")
        sys.exit(1)

    # Enregistrer le port utilisé dans un fichier AVANT de démarrer uvicorn
    try:
        with open(Path(__file__).parent / "api_port.txt", "w") as f:
            f.write(str(port))
        print(f"Port {port} enregistré dans api_port.txt")
    except Exception as e:
        print(
            f"Avertissement: Impossible d'enregistrer le port dans un fichier: {e}")

    # Utiliser la même adresse dans les messages que celle utilisée pour le binding
    host = "0.0.0.0"
    print(
        f"API sera disponible sur http://{host}:{port} (ou http://localhost:{port})")

    # Démarrer le serveur (cette fonction est bloquante)
    uvicorn.run(app, host=host, port=port)
except Exception as e:
    print(f"Erreur lors du démarrage de l'API: {e}")
    sys.exit(1)
