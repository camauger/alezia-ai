"""
Service for basic CRUD operations on characters.
"""
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from backend.models.character import CharacterCreate, CharacterModel

logger = logging.getLogger(__name__)

class CharacterService:
    """Service for character CRUD operations"""

    def create_character(self, db: Session, character: CharacterCreate) -> CharacterModel:
        """Creates a new character"""
        db_character = CharacterModel(**character.dict(exclude={"initial_traits"}))
        db.add(db_character)
        db.commit()
        db.refresh(db_character)
        logger.info(f"Character created: {db_character.name} (ID: {db_character.id})")
        return db_character

    def get_character(self, db: Session, character_id: int) -> Optional[CharacterModel]:
        """Retrieves a character by their ID"""
        return db.query(CharacterModel).options(joinedload(CharacterModel.universe)).filter(CharacterModel.id == character_id).first()

    def get_characters(self, db: Session, limit: int = None) -> list[CharacterModel]:
        """Retrieves all characters"""
        query = db.query(CharacterModel).options(joinedload(CharacterModel.universe)).order_by(CharacterModel.name)
        if limit:
            query = query.limit(limit)
        return query.all()

    def update_character(self, db: Session, character_id: int, updates: dict[str, Any]) -> Optional[CharacterModel]:
        """Updates a character"""
        db_character = self.get_character(db, character_id)
        if db_character:
            for key, value in updates.items():
                setattr(db_character, key, value)
            db.commit()
            db.refresh(db_character)
        return db_character

    def delete_character(self, db: Session, character_id: int) -> bool:
        """Deletes a character"""
        db_character = self.get_character(db, character_id)
        if db_character:
            # This will cascade delete relationships, traits, etc. if configured in the model
            db.delete(db_character)
            db.commit()
            return True
        return False

character_service = CharacterService()
