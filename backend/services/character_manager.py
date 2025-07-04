"""
Service de gestion des personnages (Facade)
"""

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.models.character import (
    Character,
    CharacterCreate,
    CharacterState,
    CharacterSummary,
    PersonalityTraits,
    TraitChange,
)

from .character_service import character_service
from .character_state_service import character_state_service
from .personality_service import PersonalityService, personality_service
from .relationship_service import relationship_service

logger = logging.getLogger(__name__)


class CharacterManager:
    """
    Gestionnaire de personnages (Facade)
    This class acts as a facade, delegating calls to the new, more focused services.
    This is a temporary measure to avoid breaking changes, and this class will be
    phased out over time.
    """

    def create_character(self, db: Session, character: CharacterCreate) -> int:
        """Creates a new character"""
        db_character = character_service.create_character(db, character)
        character_id: int = db_character.id  # type: ignore
        relationship_service.initialize_user_relationship(db, character_id)

        initial_traits = character.initial_traits or []
        personality_service.initialize_personality_traits(
            db, character_id, initial_traits
        )

        return character_id

    def get_character(self, db: Session, character_id: int) -> Optional[Character]:
        """Retrieves a character by their ID"""
        db_character = character_service.get_character(db, character_id)
        if db_character:
            return Character.from_orm(db_character)
        return None

    def get_characters(
        self, db: Session, limit: int | None = None
    ) -> list[CharacterSummary]:
        """Retrieves all characters"""
        characters = character_service.get_characters(db, limit)
        return [
            CharacterSummary.from_orm(char) for char in characters
        ]

    def update_character(
        self, db: Session, character_id: int, updates: dict[str, Any]
    ) -> bool:
        """Updates a character"""
        return character_service.update_character(db, character_id, updates) is not None

    def delete_character(self, db: Session, character_id: int) -> bool:
        """Deletes a character"""
        return character_service.delete_character(db, character_id)

    def get_character_state(self, db: Session, character_id: int) -> CharacterState:
        """Retrieve the current state of a character"""
        return character_state_service.get_character_state(db, character_id)

    def update_relationship(
        self, db: Session, character_id: int, target_name: str, updates: dict[str, Any]
    ) -> bool:
        """Updates a relationship"""
        return (
            relationship_service.update_relationship(
                db, character_id, target_name, updates
            )
            is not None
        )

    def get_personality_traits(
        self, db: Session, character_id: int
    ) -> PersonalityTraits:
        """Retrieves the personality traits of a character"""
        return personality_service.get_personality_traits(db, character_id)

    def get_trait_history(
        self, db: Session, character_id: int, trait_name: str | None = None
    ) -> list[TraitChange]:
        """Retrieves the history of trait changes for a character"""
        return personality_service.get_trait_history(db, character_id, trait_name)

    def update_trait(
        self,
        db: Session,
        character_id: int,
        trait_name: str,
        new_value: float,
        reason: str,
    ) -> bool:
        """Updates the value of a personality trait and records the change"""
        return (
            personality_service.update_trait(
                db, character_id, trait_name, new_value, reason
            )
            is not None
        )

    def update_traits_from_interaction(
        self,
        db: Session,
        character_id: int,
        interaction_text: str,
        intensity: float = 1.0,
    ) -> list[dict[str, Any]]:
        """
        Analyzes the interaction and updates personality traits based on the content
        """
        return personality_service.update_traits_from_interaction(
            db, character_id, interaction_text, intensity
        )


# Global instance of the character manager facade
character_manager = CharacterManager()
