"""
Script de vérification de l'API
"""

import sys
import os
from pathlib import Path

# Ajout du répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from utils.db import db_manager
    from models.character import CharacterCreate
    from services.character_manager import character_manager

    # Vérifier la base de données
    print("Vérification de la base de données...")

    if not os.path.exists(db_manager.db_path):
        print(f"Base de données non trouvée à l'emplacement: {db_manager.db_path}")
    else:
        print(f"Base de données trouvée: {db_manager.db_path}")

    # Tester une requête
    try:
        tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        print(f"Tables trouvées: {[t.get('name') for t in tables]}")
    except Exception as e:
        print(f"Erreur lors de la récupération des tables: {e}")

    # Tester la création d'un personnage
    print("\nTest de la création d'un personnage...")
    try:
        test_character = CharacterCreate(
            name="Test Character",
            description="Un personnage de test",
            personality="Amical et serviable"
        )

        character_id = character_manager.create_character(test_character)
        print(f"Personnage créé avec succès! ID: {character_id}")

        # Récupérer le personnage
        character = character_manager.get_character(character_id)
        print(f"Personnage récupéré: {character.name}")

        # Supprimer le personnage
        character_manager.delete_character(character_id)
        print(f"Personnage supprimé avec succès")

    except Exception as e:
        print(f"Erreur lors du test du gestionnaire de personnages: {e}")

except ImportError as e:
    print(f"Erreur d'importation: {e}")
except Exception as e:
    print(f"Erreur générale: {e}")

print("\nTest terminé")
input("Appuyez sur Entrée pour quitter...")