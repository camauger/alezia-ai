"""
Service de gestion des personnages (Facade)
"""
import logging
from typing import List, Dict, Any, Optional

from backend.models.character import Character, CharacterCreate, CharacterSummary, CharacterState, TraitChange, PersonalityTraits
from .character_service import character_service
from .relationship_service import relationship_service
from .personality_service import personality_service, PersonalityService
from .character_state_service import character_state_service

logger = logging.getLogger(__name__)

class CharacterManager:
    """
    Gestionnaire de personnages (Facade)
    This class acts as a facade, delegating calls to the new, more focused services.
    This is a temporary measure to avoid breaking changes, and this class will be
    phased out over time.
    """

    def create_character(self, character: CharacterCreate) -> int:
        """Creates a new character"""
        if character.initial_traits:
            initial_traits = character.initial_traits
        else:
            initial_traits = PersonalityService.DEFAULT_TRAITS

        character_id = character_service.create_character(character, initial_traits)
        relationship_service.initialize_user_relationship(character_id)
        personality_service.initialize_personality_traits(character_id, initial_traits)
        return character_id

    def get_character(self, character_id: int) -> Optional[Character]:
        """Retrieves a character by their ID"""
        return character_service.get_character(character_id)

    def get_characters(self, limit: int = None) -> List[CharacterSummary]:
        """Retrieves all characters"""
        return character_service.get_characters(limit)

    def update_character(self, character_id: int, updates: Dict[str, Any]) -> bool:
        """Updates a character"""
        return character_service.update_character(character_id, updates)

    def delete_character(self, character_id: int) -> bool:
        """Deletes a character"""
        return character_service.delete_character(character_id)

    def get_character_state(self, character_id: int) -> CharacterState:
        """Retrieve the current state of a character"""
        return character_state_service.get_character_state(character_id)

    def update_relationship(self, character_id: int, target_name: str, updates: Dict[str, Any]) -> bool:
        """Updates a relationship"""
        return relationship_service.update_relationship(character_id, target_name, updates)

    def get_personality_traits(self, character_id: int) -> PersonalityTraits:
        """Retrieves the personality traits of a character"""
        return personality_service.get_personality_traits(character_id)

    def get_trait_history(self, character_id: int, trait_name: str = None) -> List[TraitChange]:
        """Retrieves the history of trait changes for a character"""
        return personality_service.get_trait_history(character_id, trait_name)

    def update_trait(self, character_id: int, trait_name: str, new_value: float, reason: str) -> bool:
        """Updates the value of a personality trait and records the change"""
        return personality_service.update_trait(character_id, trait_name, new_value, reason)

    def update_traits_from_interaction(self, character_id: int, interaction_text: str, intensity: float = 1.0) -> List[Dict[str, Any]]:
        """
        Analyzes the interaction and updates personality traits based on the content
        """
        return personality_service.update_traits_from_interaction(character_id, interaction_text, intensity)


# Global instance of the character manager facade
character_manager = CharacterManager()