"""
Configuration centralisée du logging pour l'application
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

# Niveaux de journalisation personnalisés
TRACE = 5  # Niveau très détaillé pour le débogage approfondi
logging.addLevelName(TRACE, "TRACE")


def trace(self, message, *args, **kwargs):
    """Méthode de journalisation de niveau TRACE"""
    if self.isEnabledFor(TRACE):
        self._log(TRACE, message, args, **kwargs)


# Ajouter la méthode trace à la classe Logger
logging.Logger.trace = trace


def setup_logging(log_level=logging.INFO, log_to_console=True, log_to_file=True):
    """Configuration globale du logging pour l'application"""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Supprimer les handlers existants pour éviter les doublons
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Format de journalisation
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Journalisation dans la console
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

    # Journalisation dans un fichier
    if log_to_file:
        log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        os.makedirs(log_dir, exist_ok=True)

        # Nom du fichier basé sur la date
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"alezia-{today}.log"

        # Rotation des fichiers de log (10 Mo max, 10 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=10, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    return logger


def get_logger(name):
    """Récupère un logger avec le nom spécifié"""
    return logging.getLogger(name)


# Configuration de journalisation par défaut pour les requêtes HTTP
def configure_http_logging():
    """Configure la journalisation spécifique pour les requêtes HTTP"""
    # Réduire le niveau de journalisation pour les bibliothèques bruyantes
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # Journalisation détaillée pour nos propres modules
    logging.getLogger("backend").setLevel(logging.DEBUG)


# Configuration de journalisation pour les performances
class PerformanceLogger:
    """Utilitaire pour mesurer et journaliser les performances"""

    def __init__(self, logger, prefix=""):
        self.logger = logger
        self.prefix = prefix
        self.start_times = {}

    def start(self, operation):
        """Démarre le chronométrage d'une opération"""
        import time
        operation_key = f"{self.prefix}{operation}"
        self.start_times[operation_key] = time.time()
        self.logger.debug(f"Début de l'opération: {operation}")

    def end(self, operation, success=True):
        """Termine le chronométrage et journalise le temps écoulé"""
        import time
        operation_key = f"{self.prefix}{operation}"
        if operation_key in self.start_times:
            elapsed = time.time() - self.start_times[operation_key]
            status = "terminée avec succès" if success else "échouée"
            self.logger.info(
                f"Opération {operation} {status} en {elapsed:.3f}s")
            del self.start_times[operation_key]
        else:
            self.logger.warning(
                f"Tentative de terminer une opération non démarrée: {operation}")


# Initialisation globale du logging au démarrage du module
setup_logging()
