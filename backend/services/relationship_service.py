"""
Service for managing relationships between characters and the user.
"""

import datetime
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.models.relationship import RelationshipCreate, RelationshipModel

logger: logging.Logger = logging.getLogger(__name__)


class RelationshipService:
    """Service for managing relationships"""

    def initialize_user_relationship(
        self, db: Session, character_id: int
    ) -> RelationshipModel:
        """Initializes a relationship between the character and the user"""
        relationship = RelationshipCreate(
            character_id=character_id,
            target_name='user',
            sentiment=0.0,
            trust=0.3,
            familiarity=0.1,
            notes='Initial relationship with the user',
        )
        db_relationship = RelationshipModel(**relationship.model_dump())
        db.add(db_relationship)
        db.commit()
        db.refresh(db_relationship)
        return db_relationship

    def update_relationship(
        self, db: Session, character_id: int, target_name: str, updates: dict[str, Any]
    ) -> Optional[RelationshipModel]:
        """Updates a relationship"""
        db_relationship = (
            db.query(RelationshipModel)
            .filter(
                RelationshipModel.character_id == character_id,
                RelationshipModel.target_name == target_name,
            )
            .first()
        )

        if db_relationship:
            for key, value in updates.items():
                setattr(db_relationship, key, value)
            db_relationship.last_updated = datetime.datetime.now()  # type: ignore
            db.commit()
            db.refresh(db_relationship)
        return db_relationship


relationship_service = RelationshipService()
