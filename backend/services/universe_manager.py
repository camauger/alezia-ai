"""Universe and element manager"""

import logging
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.character import CharacterModel
from backend.models.universe import (
    UniverseCreate,
    UniverseDetail,
    UniverseElementCreate,
    UniverseElementModel,
    UniverseModel,
    UniverseSummary,
)

logger = logging.getLogger(__name__)


class UniverseManager:
    """Universe manager"""

    def create_universe(self, db: Session, universe: UniverseCreate) -> UniverseModel:
        """Creates a new universe"""
        db_universe = UniverseModel(**universe.model_dump())
        db.add(db_universe)
        db.commit()
        db.refresh(db_universe)
        logger.info(f'Universe created: {db_universe.name} (ID: {db_universe.id})')
        return db_universe

    def get_universe(self, db: Session, universe_id: int) -> Optional[UniverseModel]:
        """Retrieves a universe by its ID"""
        return db.query(UniverseModel).filter(UniverseModel.id == universe_id).first()

    def get_universes(self, db: Session) -> list[UniverseSummary]:
        """Retrieves all universes with a summary"""
        results = (
            db.query(
                UniverseModel.id,
                UniverseModel.name,
                UniverseModel.type,
                UniverseModel.time_period,
                func.count(CharacterModel.id).label('character_count'),
            )
            .outerjoin(CharacterModel, UniverseModel.id == CharacterModel.universe_id)
            .group_by(UniverseModel.id)
            .order_by(UniverseModel.name)
            .all()
        )

        return [UniverseSummary(**result) for result in results]

    def get_universe_details(
        self, db: Session, universe_id: int
    ) -> Optional[UniverseDetail]:
        """Retrieves the complete details of a universe with its elements and characters"""
        universe = self.get_universe(db, universe_id)
        if not universe:
            return None

        return UniverseDetail.from_orm(universe)

    def update_universe(
        self, db: Session, universe_id: int, updates: dict[str, Any]
    ) -> Optional[UniverseModel]:
        """Updates a universe"""
        db_universe = self.get_universe(db, universe_id)
        if db_universe:
            for key, value in updates.items():
                setattr(db_universe, key, value)
            db.commit()
            db.refresh(db_universe)
        return db_universe

    def delete_universe(self, db: Session, universe_id: int) -> bool:
        """Deletes a universe"""
        db_universe = self.get_universe(db, universe_id)
        if db_universe:
            db.delete(db_universe)
            db.commit()
            return True
        return False

    def add_universe_element(
        self, db: Session, element: UniverseElementCreate
    ) -> UniverseElementModel:
        """Adds an element to a universe"""
        db_element = UniverseElementModel(**element.model_dump())
        db.add(db_element)
        db.commit()
        db.refresh(db_element)
        return db_element

    def get_universe_element(
        self, db: Session, element_id: int
    ) -> Optional[UniverseElementModel]:
        """Retrieves a universe element by its ID"""
        return (
            db.query(UniverseElementModel)
            .filter(UniverseElementModel.id == element_id)
            .first()
        )

    def get_universe_elements(
        self, db: Session, universe_id: int
    ) -> list[UniverseElementModel]:
        """Retrieves all elements of a universe"""
        return (
            db.query(UniverseElementModel)
            .filter(UniverseElementModel.universe_id == universe_id)
            .order_by(UniverseElementModel.importance.desc(), UniverseElementModel.name)
            .all()
        )

    def update_universe_element(
        self, db: Session, element_id: int, updates: dict[str, Any]
    ) -> Optional[UniverseElementModel]:
        """Updates a universe element"""
        db_element = self.get_universe_element(db, element_id)
        if db_element:
            for key, value in updates.items():
                setattr(db_element, key, value)
            db.commit()
            db.refresh(db_element)
        return db_element

    def delete_universe_element(self, db: Session, element_id: int) -> bool:
        """Deletes a universe element"""
        db_element = self.get_universe_element(db, element_id)
        if db_element:
            db.delete(db_element)
            db.commit()
            return True
        return False

    def get_universe_description(self, db: Session, universe_id: int) -> str:
        """Generates a complete description of the universe with its elements"""
        universe = self.get_universe(db, universe_id)
        if not universe:
            return ''

        elements = self.get_universe_elements(db, universe_id)

        description = f'Universe name: {universe.name}\n'
        description += f'Description: {universe.description}\n'

        if universe.time_period:
            description += f'Period: {universe.time_period}\n'

        if universe.rules:
            description += f'Rules: {universe.rules}\n'

        if elements:
            description += '\nImportant elements of this universe:\n'

            # Sort by element type
            elements_by_type = {}
            for element in elements:
                if element.type not in elements_by_type:
                    elements_by_type[element.type] = []
                elements_by_type[element.type].append(element)

            for element_type, type_elements in elements_by_type.items():
                description += f'\n{element_type.capitalize()}s:\n'
                for element in type_elements:
                    description += f'- {element.name}: {element.description}\n'

        return description


# Global instance of the universe manager
universe_manager = UniverseManager()
