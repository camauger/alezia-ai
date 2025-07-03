"""
Service for determining a character's current state (mood, etc.).
"""
import logging
import datetime
from typing import List, Dict, Any

from backend.utils.db import db_manager
from backend.models.character import CharacterState
from .memory_manager import memory_manager
from .personality_service import personality_service
from .character_service import character_service

logger = logging.getLogger(__name__)

class CharacterStateService:
    """Service for determining character state"""

    def get_character_state(self, character_id: int) -> CharacterState:
        """Retrieves the current state of a character"""
        character = character_service.get_character(character_id)
        if not character:
            raise ValueError(f"Personnage introuvable (ID: {character_id})")

        # Récupérer la relation avec l'utilisateur
        query = "SELECT * FROM relationships WHERE character_id = ? AND target_name = 'user'"
        relationships = db_manager.execute_query(
            query, (character_id,), fetchall=True)

        relationship = relationships[0] if relationships else {  # type: ignore
            "sentiment": 0.0,
            "trust": 0.0,
            "familiarity": 0.0
        }

        # Récupérer les mémoires récentes
        recent_memories = memory_manager.get_memories(character_id, limit=10)
        recent_memories_dict = [memory.dict() for memory in recent_memories]

        # Récupérer les traits actifs
        active_traits = personality_service.get_personality_traits_as_dict(character_id)

        # Déterminer l'humeur en fonction des mémoires, relations et traits de personnalité
        mood = self._determine_mood(
            relationship, recent_memories_dict, active_traits)

        return CharacterState(
            character_id=character_id,
            mood=mood,
            current_context={
                "universe": character.universe,
                "last_interaction": datetime.datetime.now().isoformat()
            },
            recent_memories=recent_memories_dict,
            relationship_to_user={
                "sentiment": relationship.get("sentiment", 0.0),
                "trust": relationship.get("trust", 0.0),
                "familiarity": relationship.get("familiarity", 0.0)
            },
            active_traits=active_traits
        )

    def _determine_mood(self, relationship: Dict[str, Any], recent_memories: List[Dict[str, Any]],
                        traits: Dict[str, float] = None) -> str:
        """Determines the character's mood based on their relationship, recent memories, and personality traits"""
        # Sentiment de base à partir de la relation
        sentiment = relationship.get("sentiment", 0.0)
        base_mood_score = sentiment

        # Ajuster en fonction des traits de personnalité si disponibles
        if traits:
            # La stabilité émotionnelle atténue l'effet du sentiment (positif ou négatif)
            if "stabilité émotionnelle" in traits:
                stabilité = traits["stabilité émotionnelle"]
                # Plus stable = moins influencé par le sentiment, plus neutre
                base_mood_score = base_mood_score * (1 - abs(stabilité) * 0.5)

            # L'extraversion augmente la tendance à être plus joyeux
            if "extraversion" in traits:
                extraversion = traits["extraversion"]
                base_mood_score += extraversion * 0.3

            # L'impulsivité accentue l'humeur actuelle dans les deux sens
            if "impulsivité" in traits:
                impulsivité = traits["impulsivité"]
                if base_mood_score > 0:
                    base_mood_score += impulsivité * 0.2
                elif base_mood_score < 0:
                    base_mood_score -= impulsivité * 0.2

        # Déterminer l'humeur en fonction du score final
        if base_mood_score > 0.7:
            return "cheerful"
        elif base_mood_score > 0.3:
            return "friendly"
        elif base_mood_score > -0.3:
            return "neutral"
        elif base_mood_score > -0.7:
            return "annoyed"
        else:
            return "angry"

character_state_service = CharacterStateService()