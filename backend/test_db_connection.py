#!/usr/bin/env python3

"""
Script de test pour vérifier la connexion à la base de données.
Exécuter ce script pour s'assurer que les modifications du système d'accès à la base
de données fonctionnent correctement.
"""

import logging
import sys
from pathlib import Path

from utils.db import db_manager

# Ajouter le répertoire parent au chemin Python pour permettre les imports absolus
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importer le gestionnaire de base de données


def test_db_connection():
    """Teste la connexion à la base de données"""
    try:
        # Vérifier si la table 'characters' existe
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name='characters'"
        result = db_manager.execute_query(query)

        if result:
            logger.info(
                "✅ La table 'characters' existe dans la base de données.")
        else:
            logger.warning(
                "⚠️ La table 'characters' n'existe pas dans la base de données.")

        # Compte le nombre de tables dans la base de données
        query = "SELECT count(*) as table_count FROM sqlite_master WHERE type='table'"
        result = db_manager.execute_query(query)
        table_count = result[0]['table_count'] if result else 0

        logger.info(f"📊 La base de données contient {table_count} tables.")

        # Liste toutes les tables
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        tables = db_manager.execute_query(query)

        logger.info("📋 Tables dans la base de données:")
        for table in tables:
            logger.info(f"  - {table['name']}")

            # Pour chaque table, compte le nombre d'enregistrements
            count_query = f"SELECT count(*) as record_count FROM {table['name']}"
            try:
                count_result = db_manager.execute_query(count_query)
                record_count = count_result[0]['record_count'] if count_result else 0
                logger.info(f"    • {record_count} enregistrements")
            except Exception as e:
                logger.error(
                    f"    • Erreur lors du comptage des enregistrements: {e}")

        return True

    except Exception as e:
        logger.error(
            f"❌ Erreur lors du test de connexion à la base de données: {e}")
        return False


if __name__ == "__main__":
    logger.info("🔍 Test de connexion à la base de données...")
    success = test_db_connection()

    if success:
        logger.info("✅ Test de connexion à la base de données réussi!")
        sys.exit(0)
    else:
        logger.error("❌ Test de connexion à la base de données échoué!")
        sys.exit(1)
