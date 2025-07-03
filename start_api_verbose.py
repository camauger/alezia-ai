"""
Script verbeux pour démarrer l'API Alezia AI et capturer les erreurs
"""

import logging
import sys
import traceback
from pathlib import Path

import uvicorn

# Configuration du logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
PORT = 8005  # Utiliser un port différent pour éviter les conflits
HOST = "0.0.0.0"

# Ajouter le répertoire courant au chemin Python
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

logger.info(
    f"Démarrage en mode debug de l'API Alezia AI sur le port {PORT}...")
logger.info(f"Répertoire courant: {current_dir}")
logger.info(f"Python path: {sys.path}")

# Vérifier les imports
try:
    logger.debug("Tentative d'importation du module backend.app...")
    import backend.app
    logger.info("Module backend.app importé avec succès")

    logger.debug(
        "Tentative d'importation du module backend.routes.characters...")
    import backend.routes.characters
    logger.info("Module backend.routes.characters importé avec succès")

    logger.debug("Tentative d'importation du module backend.utils.db...")
    import backend.utils.db
    logger.info("Module backend.utils.db importé avec succès")

    logger.debug("Tentative d'initialisation de la base de données...")
    db_manager = backend.utils.db.db_manager
    db_manager._initialize_schema()
    logger.info(f"Base de données initialisée à {db_manager.db_path}")
except Exception as e:
    logger.critical(f"Erreur lors de l'initialisation: {e}")
    logger.critical(traceback.format_exc())
    sys.exit(1)

# Enregistrer le port dans un fichier pour que le frontend puisse le lire
try:
    with open("api_port.txt", "w") as f:
        f.write(str(PORT))
    logger.info(f"Port {PORT} enregistré dans api_port.txt")
except Exception as e:
    logger.error(f"Erreur lors de l'enregistrement du port: {e}")

# Démarrer l'API
try:
    logger.info("Démarrage du serveur uvicorn...")
    # Démarrer l'application directement depuis backend/app.py
    uvicorn.run(
        "backend.app:app",
        host=HOST,
        port=PORT,
        reload=False,  # Désactiver reload pour éviter les problèmes
        log_level="debug"
    )
except KeyboardInterrupt:
    logger.info("Arrêt manuel du serveur")
except Exception as e:
    logger.critical(f"Erreur lors du démarrage de l'API: {e}")
    logger.critical(traceback.format_exc())
    sys.exit(1)
