"""
Service for determining a character's current state (mood, etc.).
"""

import datetime
import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.models.character import CharacterState
from backend.models.relationship import RelationshipModel

from .character_service import character_service
from .memory_manager import memory_manager
from .personality_service import personality_service

logger = logging.getLogger(__name__)


class CharacterStateService:
    """Service for determining character state"""

    def get_character_state(self, db: Session, character_id: int) -> CharacterState:
        """Retrieves the current state of a character"""
        character = character_service.get_character(db, character_id)
        if not character:
            raise ValueError(f'Character not found (ID: {character_id})')

        # Retrieve the relationship with the user
        relationship = (
            db.query(RelationshipModel)
            .filter(
                RelationshipModel.character_id == character_id,
                RelationshipModel.target_name == 'user',
            )
            .first()
        )

        relationship_data = {
            'sentiment': relationship.sentiment if relationship else 0.0,
            'trust': relationship.trust if relationship else 0.0,
            'familiarity': relationship.familiarity if relationship else 0.0,
        }

        # Retrieve recent memories
        recent_memories = memory_manager.get_memories(db, character_id, limit=10)
        recent_memories_dict = [memory.model_dump() for memory in recent_memories]

        # Retrieve active traits
        active_traits = personality_service.get_personality_traits_as_dict(
            db, character_id
        )

        # Determine mood based on memories, relationships, and personality traits
        mood = self._determine_mood(
            relationship_data, recent_memories_dict, active_traits
        )

        return CharacterState(
            character_id=character_id,
            mood=mood,
            current_context={
                'universe': character.universe.name if character.universe else None,
                'last_interaction': datetime.datetime.now().isoformat(),
            },
            recent_memories=recent_memories_dict,
            relationship_to_user=relationship_data,
            active_traits=active_traits,
        )

    def _determine_mood(
        self,
        relationship: dict[str, Any],
        recent_memories: list[dict[str, Any]],
        traits: dict[str, float] | None = None,
    ) -> str:
        """Determines the character's mood based on their relationship, recent memories, and personality traits"""
        # ... (same as before)
        sentiment = relationship.get('sentiment', 0.0)
        base_mood_score = sentiment

        if traits:
            if 'stabilité émotionnelle' in traits:
                stabilité = traits['stabilité émotionnelle']
                base_mood_score = base_mood_score * (1 - abs(stabilité) * 0.5)
            if 'extraversion' in traits:
                extraversion = traits['extraversion']
                base_mood_score += extraversion * 0.3
            if 'impulsivité' in traits:
                impulsivité = traits['impulsivité']
                if base_mood_score > 0:
                    base_mood_score += impulsivité * 0.2
                elif base_mood_score < 0:
                    base_mood_score -= impulsivité * 0.2

        if base_mood_score > 0.7:
            return 'cheerful'
        elif base_mood_score > 0.3:
            return 'friendly'
        elif base_mood_score > -0.3:
            return 'neutral'
        elif base_mood_score > -0.7:
            return 'annoyed'
        else:
            return 'angry'


character_state_service = CharacterStateService()
