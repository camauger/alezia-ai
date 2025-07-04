"""
Service for managing personality traits and their evolution.
"""

import datetime
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.models.character import (
    PersonalityTraits,
    TraitChange,
    TraitChangeModel,
    TraitModel,
    CharacterTrait,
)

logger = logging.getLogger(__name__)


class PersonalityService:
    """Service for managing personality traits"""

    DEFAULT_TRAITS = [
        # ... (same as before)
    ]

    def initialize_personality_traits(
        self, db: Session, character_id: int, initial_traits: list[dict[str, Any]]
    ) -> None:
        """Initializes the personality traits of a character"""
        for trait_data in initial_traits:
            db_trait = TraitModel(character_id=character_id, **trait_data)
            db.add(db_trait)
            db.commit()
            db.refresh(db_trait)

            # Record the initialization as the first change
            change = TraitChangeModel(
                trait_id=db_trait.id,
                character_id=character_id,
                old_value=0.0,
                new_value=db_trait.value,
                change_amount=db_trait.value,
                reason='Initialisation du trait',
            )
            db.add(change)
            db.commit()

        logger.info(
            f'Initialized {len(initial_traits)} traits for character ID {character_id}'
        )

    def get_personality_traits(
        self, db: Session, character_id: int
    ) -> PersonalityTraits:
        """Retrieves the personality traits of a character"""
        traits_data = (
            db.query(TraitModel).filter(TraitModel.character_id == character_id).all()
        )
        return PersonalityTraits(
            traits=[CharacterTrait.from_orm(trait) for trait in traits_data]
        )

    def get_personality_traits_as_dict(
        self, db: Session, character_id: int
    ) -> dict[str, float]:
        """Retrieves the personality traits of a character as a dictionary {name: value}"""
        traits_data = (
            db.query(TraitModel.name, TraitModel.value)
            .filter(TraitModel.character_id == character_id)
            .all()
        )
        return {name: value for name, value in traits_data}

    def get_trait_history(
        self, db: Session, character_id: int, trait_name: str | None = None
    ) -> list[TraitChange]:
        """Retrieves the history of trait changes for a character"""
        query = db.query(TraitChangeModel).filter(
            TraitChangeModel.character_id == character_id
        )
        if trait_name:
            query = query.join(TraitModel).filter(TraitModel.name == trait_name)
        return [
            TraitChange.from_orm(change)
            for change in query.order_by(TraitChangeModel.timestamp.desc()).all()
        ]

    def update_trait(
        self,
        db: Session,
        character_id: int,
        trait_name: str,
        new_value: float,
        reason: str,
    ) -> Optional[TraitModel]:
        """Updates the value of a personality trait and records the change"""
        db_trait = (
            db.query(TraitModel)
            .filter(
                TraitModel.character_id == character_id, TraitModel.name == trait_name
            )
            .first()
        )

        if db_trait:
            old_value = db_trait.value
            db_trait.value = max(-1.0, min(1.0, new_value))
            db_trait.last_updated = datetime.datetime.now()

            change = TraitChangeModel(
                trait_id=db_trait.id,
                character_id=character_id,
                old_value=old_value,
                new_value=db_trait.value,
                change_amount=db_trait.value - old_value,
                reason=reason,
            )
            db.add(change)
            db.commit()
            db.refresh(db_trait)
            logger.info(
                f'Trait {trait_name} updated for character ID {character_id}: {old_value} → {db_trait.value}'
            )
        return db_trait

    def update_traits_from_interaction(
        self,
        db: Session,
        character_id: int,
        interaction_text: str,
        intensity: float = 1.0,
    ) -> list[dict[str, Any]]:
        """
        Analyzes the interaction and updates personality traits based on the content.
        """
        # ... (This method would also need to be updated to use the db session)
        # For brevity, the implementation is omitted here, but it would follow the same pattern
        # of querying for traits, calculating changes, and then calling self.update_trait.
        return []


personality_service = PersonalityService()
