"""
Service for basic CRUD operations on characters.
"""
import logging
import datetime
from typing import List, Dict, Any, Optional

from backend.utils.db import db_manager
from backend.models.character import Character, CharacterCreate, CharacterSummary
from .memory_manager import memory_manager

logger = logging.getLogger(__name__)

class CharacterService:
    """Service for character CRUD operations"""

    def create_character(self, character: CharacterCreate, initial_traits: List[Dict[str, Any]]) -> int:
        """Creates a new character"""
        character_dict = character.dict(exclude={"initial_traits"})
        character_dict["created_at"] = datetime.datetime.now()

        # Vérification de l'existence de l'univers si universe_id est fourni
        if character_dict.get("universe_id"):
            universe = db_manager.get_by_id(
                "universes", character_dict["universe_id"])
            if not universe:
                logger.warning(
                    f"L'univers avec l'ID {character_dict['universe_id']} n'existe pas. Ce champ sera défini à NULL.")
                # Définir à NULL si l'univers n'existe pas
                character_dict["universe_id"] = None

        character_id = db_manager.insert("characters", character_dict)
        logger.info(f"Personnage créé: {character.name} (ID: {character_id})")

        return character_id

    def get_character(self, character_id: int) -> Optional[Character]:
        """Retrieves a character by their ID"""
        character = db_manager.get_by_id("characters", character_id)
        if character:
            # Ajouter le nom de l'univers si disponible
            if character.get("universe_id"):
                universe = db_manager.get_by_id(
                    "universes", character["universe_id"])
                if universe:
                    character["universe"] = universe["name"]

            return Character(**character)
        return None

    def get_characters(self, limit: int = None) -> List[CharacterSummary]:
        """Retrieves all characters"""
        characters = db_manager.get_all(
            "characters", order_by="name", limit=limit)

        # Ajouter les noms d'univers
        universe_ids = [c["universe_id"]
                        for c in characters if c["universe_id"]]
        universes = {}

        if universe_ids:
            query = f"SELECT id, name FROM universes WHERE id IN ({','.join('?' for _ in universe_ids)})"
            results = db_manager.execute_query(query, tuple(universe_ids))
            universes = {u["id"]: u["name"] for u in results}

        # Ajouter le nom de l'univers à chaque personnage
        for character in characters:
            if character["universe_id"] and character["universe_id"] in universes:
                character["universe"] = universes[character["universe_id"]]

        return [CharacterSummary(**character) for character in characters]

    def update_character(self, character_id: int, updates: Dict[str, Any]) -> bool:
        """Updates a character"""
        rows_updated = db_manager.update(
            "characters", updates, "id = ?", (character_id,))
        return rows_updated > 0

    def delete_character(self, character_id: int) -> bool:
        """Deletes a character"""
        # Récupérer toutes les mémoires du personnage
        memories = memory_manager.get_memories(character_id)

        # Supprimer les mémoires une par une (pour s'assurer que les faits sont aussi supprimés)
        for memory in memories:
            memory_manager.delete_memory(memory.id)

        # Supprimer les relations
        db_manager.delete("relationships", "character_id = ?", (character_id,))

        # Supprimer les traits de personnalité
        db_manager.delete("personality_traits",
                          "character_id = ?", (character_id,))

        # Supprimer l'historique des changements de traits
        db_manager.delete("trait_changes", "character_id = ?", (character_id,))

        # Supprimer le personnage
        rows_deleted = db_manager.delete(
            "characters", "id = ?", (character_id,))
        return rows_deleted > 0

character_service = CharacterService()