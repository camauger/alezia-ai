"""
Tests unitaires pour le gestionnaire de personnages
"""

import datetime
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.models.character import CharacterCreate
from backend.services.character_manager import CharacterManager

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def db_manager_mock():
    """Fixture pour mocker le gestionnaire de base de données"""
    with patch("backend.services.character_manager.db_manager") as mock:
        # Configurer le mock pour retourner un ID lors de l'insertion
        mock.insert.return_value = 1

        # Configurer le mock pour get_by_id
        mock.get_by_id.side_effect = lambda table, id: (
            {"id": 1, "name": "Test Universe"} if table == "universes" else None
        )

        yield mock


@pytest.fixture
def character_manager(db_manager_mock):
    """Fixture pour créer une instance de CharacterManager avec des mocks"""
    with patch("backend.services.character_manager.memory_manager"):
        return CharacterManager()


def test_create_character(character_manager, db_manager_mock):
    """Test de la création d'un personnage"""
    # Créer un personnage de test
    character = CharacterCreate(
        name="Test Character",
        description="A test character",
        personality="Friendly",
        universe_id=1,
        backstory=None,
        initial_traits=None,
    )

    # Appeler la méthode à tester
    character_id = character_manager.create_character(character)

    # Vérifier que l'insertion a été appelée
    db_manager_mock.insert.assert_called()

    # Vérifier que l'ID retourné est correct
    assert character_id == 1


def test_create_character_invalid_universe(character_manager, db_manager_mock):
    """Test de la création d'un personnage avec un univers invalide"""
    # Configurer le mock pour retourner None pour l'univers
    db_manager_mock.get_by_id.return_value = None

    # Créer un personnage de test avec un univers inexistant
    character = CharacterCreate(
        name="Test Character",
        description="A test character",
        personality="Friendly",
        universe_id=999,  # ID inexistant
        backstory=None,
        initial_traits=None,
    )

    # Appeler la méthode à tester
    character_id = character_manager.create_character(character)

    # Vérifier que l'insertion a été appelée avec universe_id=None
    args, kwargs = db_manager_mock.insert.call_args
    assert args[1]["universe_id"] is None

    # Vérifier que l'ID retourné est correct
    assert character_id == 1


def test_get_character(character_manager, db_manager_mock):
    """Test de la récupération d'un personnage"""
    # Configurer le mock pour retourner un personnage
    db_manager_mock.get_by_id.return_value = {
        "id": 1,
        "name": "Test Character",
        "description": "A test character",
        "personality": "Friendly",
        "backstory": None,
        "universe_id": 1,
        "created_at": datetime.datetime.now().isoformat(),
    }

    # Appeler la méthode à tester
    character = character_manager.get_character(1)

    # Vérifier que le get_by_id a été appelé
    db_manager_mock.get_by_id.assert_called_with("characters", 1)

    # Vérifier que le personnage retourné est correct
    assert character is not None
    assert character.name == "Test Character"


if __name__ == "__main__":
    pytest.main()
