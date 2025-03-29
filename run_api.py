"""
Script simple pour démarrer l'API
"""

from backend.config import API_CONFIG
import os
import sys
import socket
import uvicorn
import logging
from pathlib import Path
import argparse
import signal
from time import sleep
import requests

# Configurer les chemins d'importation
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir / "backend"
sys.path.append(str(current_dir))
sys.path.append(str(backend_dir))

# Importer la configuration

# Constantes
LISTEN_HOST = "0.0.0.0"  # Écoute sur toutes les interfaces


def is_port_available(port):
    """Vérifie si un port est disponible"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((LISTEN_HOST, port))
            return True
        except socket.error:
            return False


def find_available_port(start_port, end_port):
    """Trouve un port disponible dans la plage spécifiée"""
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return None


def save_port_to_file(port):
    """Sauvegarde le port utilisé dans un fichier pour que le frontend puisse le lire"""
    try:
        with open(API_CONFIG["port_file"], "w") as f:
            f.write(str(port))
        print(f"Port {port} enregistré dans {API_CONFIG['port_file']}")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du port: {e}")


def initialize_database():
    """Initialise la base de données et les données par défaut"""
    try:
        from backend.utils.db import db_manager
        # Forcer l'initialisation du schéma
        db_manager._initialize_schema()
        # Assurer la présence d'un univers par défaut
        universe_id = db_manager.ensure_default_universe()
        if universe_id:
            print(f"Univers par défaut initialisé avec ID: {universe_id}")

        # Vérifier si des personnages existent
        characters = db_manager.get_all("characters")
        print(
            f"Nombre de personnages dans la base de données: {len(characters)}")

        if characters:
            for character in characters:
                print(
                    f"Personnage existant: ID={character['id']}, Nom={character['name']}")

        return True
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        return False


def check_api_health(port, max_attempts=20):
    """Vérifie que l'API répond correctement sur le port spécifié"""
    url = f"http://localhost:{port}/health"
    print(f"Vérification de la santé de l'API à {url}...")

    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print(
                        f"API correctement démarrée et prête (tentative {attempt+1}/{max_attempts})")
                    return True
        except requests.RequestException:
            pass

        # Attendre avant la prochaine tentative
        sleep(0.5)

        if attempt < max_attempts - 1:
            print(
                f"L'API n'est pas encore prête, nouvelle tentative ({attempt+1}/{max_attempts})...")

    print(
        f"AVERTISSEMENT: Impossible de confirmer le démarrage de l'API après {max_attempts} tentatives")
    return False


def handle_exit(sig, frame):
    print("\nArrêt propre de l'API...")
    sys.exit(0)


# Configuration des gestionnaires de signaux pour le thread principal
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# Point d'entrée principal
if __name__ == "__main__":
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
            import requests
        except ImportError:
            print(
                "ERREUR: uvicorn ou requests n'est pas installé. Exécutez 'pip install uvicorn requests'.")
            sys.exit(1)

        parser = argparse.ArgumentParser(
            description="Démarrage de l'API Alezia")
        parser.add_argument(
            "--port", type=int, help="Port à utiliser (laissez vide pour auto-détection)")
        args = parser.parse_args()

        # Initialiser la base de données
        if not initialize_database():
            print("ERREUR: Échec de l'initialisation de la base de données.")
            sys.exit(1)

        # Trouver un port disponible
        port_range = API_CONFIG.get("port_range", [8000, 8020])

        if args.port:
            if not is_port_available(args.port):
                print(f"ERREUR: Le port {args.port} n'est pas disponible.")
                sys.exit(1)
            port = args.port
        else:
            port = find_available_port(port_range[0], port_range[1])

        if not port:
            print(
                f"ERREUR: Aucun port disponible dans la plage {port_range[0]}-{port_range[1]}")
            sys.exit(1)

        # Sauvegarder le port pour le frontend
        save_port_to_file(port)

        print(
            f"API sera disponible sur http://{API_CONFIG['host']}:{port} (ou http://localhost:{port})")
        print(
            f"Documentation sera disponible sur http://localhost:{port}/docs")

        # Démarrer le serveur dans le thread principal
        uvicorn.run(
            "backend.app:app",
            host=API_CONFIG["host"],
            port=port,
            reload=API_CONFIG.get("debug", False),
            workers=API_CONFIG.get("workers", 1),
        )

    except Exception as e:
        print(f"Erreur lors du démarrage de l'API: {e}")
        sys.exit(1)
