"""
Service for managing relationships between characters and the user.
"""
import logging
import datetime
from typing import Dict, Any

from backend.utils.db import db_manager
from backend.models.relationship import RelationshipCreate

logger = logging.getLogger(__name__)

class RelationshipService:
    """Service for managing relationships"""

    def initialize_user_relationship(self, character_id: int) -> int:
        """Initializes a relationship between the character and the user"""
        relationship = RelationshipCreate(
            character_id=character_id,
            target_name="user",
            sentiment=0.0,  # Neutre au départ
            trust=0.3,      # Confiance initiale modérée
            familiarity=0.1,  # Faible familiarité au départ
            notes="Relation initiale avec l'utilisateur"
        )

        relationship_dict = relationship.dict()
        relationship_dict["last_updated"] = datetime.datetime.now()

        relationship_id = db_manager.insert("relationships", relationship_dict)
        return relationship_id

    def update_relationship(self, character_id: int, target_name: str, updates: Dict[str, Any]) -> bool:
        """Updates a relationship"""
        # Vérifier si la relation existe
        query = "SELECT * FROM relationships WHERE character_id = ? AND target_name = ?"
        relationships = db_manager.execute_query(
            query, (character_id, target_name), fetchall=True)

        updates["last_updated"] = datetime.datetime.now()

        if relationships:
            # Mettre à jour la relation existante
            condition = "character_id = ? AND target_name = ?"
            params = (character_id, target_name)
            return db_manager.update("relationships", updates, condition, params) > 0
        else:
            # Créer une nouvelle relation
            relationship_data = {
                "character_id": character_id,
                "target_name": target_name,
                "sentiment": 0.0,
                "trust": 0.0,
                "familiarity": 0.0,
                "last_updated": datetime.datetime.now()
            }
            relationship_data.update(updates)
            return db_manager.insert("relationships", relationship_data) > 0

relationship_service = RelationshipService()