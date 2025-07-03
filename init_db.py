"""
Script d'initialisation de la base de données
Crée les structures nécessaires et ajoute un univers par défaut
"""

import datetime
import sys
from pathlib import Path

# Ajouter le dossier backend au PYTHONPATH
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

print("Initialisation de la base de données Alezia AI...")

# Importer les modules nécessaires
try:
    from utils.db import db_manager
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    sys.exit(1)

# Vérifier si la table universes existe


def check_universes_table():
    try:
        result = db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='universes'")
        return len(result) > 0
    except Exception as e:
        print(f"Erreur lors de la vérification de la table universes: {e}")
        return False

# Vérifier si des univers existent déjà


def get_universe_count():
    try:
        if not check_universes_table():
            return 0
        result = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM universes")
        return result[0]['count'] if result else 0
    except Exception as e:
        print(f"Erreur lors du comptage des univers: {e}")
        return 0

# Créer un univers par défaut


def create_default_universe():
    try:
        universe_data = {
            "name": "Monde moderne",
            "description": "Un univers contemporain similaire au monde réel actuel",
            "type": "réaliste",
            "time_period": "2024",
            "rules": "Lois de la physique standards, technologies modernes disponibles",
            "created_at": datetime.datetime.now().isoformat()
        }

        universe_id = db_manager.insert("universes", universe_data)
        print(f"Univers par défaut créé avec l'ID: {universe_id}")
        return universe_id
    except Exception as e:
        print(f"Erreur lors de la création de l'univers par défaut: {e}")
        return None


# Exécution principale
if __name__ == "__main__":
    universe_count = get_universe_count()

    if universe_count == 0:
        print("Aucun univers trouvé. Création d'un univers par défaut...")
        universe_id = create_default_universe()
        if universe_id:
            print("Base de données initialisée avec succès.")
        else:
            print("Échec de l'initialisation de la base de données.")
    else:
        print(f"{universe_count} univers déjà présents dans la base de données.")
        print("Aucune action nécessaire.")

    # Afficher les tables disponibles
    try:
        tables = db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [table['name'] for table in tables]
        print(f"Tables disponibles: {', '.join(table_names)}")
    except Exception as e:
        print(f"Erreur lors de la récupération des tables: {e}")

    print("\nInitialisation terminée.")
