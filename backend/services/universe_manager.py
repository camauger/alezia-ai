"""
Universe and element manager
"""

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.models.universe import (
    Universe,
    UniverseCreate,
    UniverseDetail,
    UniverseElement,
    UniverseElementCreate,
    UniverseSummary,
)
from backend.utils.db import db_manager  # type: ignore

logger = logging.getLogger(__name__)


class UniverseManager:
    """Universe manager"""

    def create_universe(self, universe: UniverseCreate) -> int:
        """Creates a new universe"""
        universe_dict = universe.model_dump()
        universe_id = db_manager.insert("universes", universe_dict)
        logger.info(f"Universe created: {universe.name} (ID: {universe_id})")
        return universe_id

    def get_universe(self, universe_id: int) -> Optional[Universe]:
        """Retrieves a universe by its ID"""
        universe = db_manager.get_by_id("universes", universe_id)
        if universe:
            return Universe(**universe)
        return None

    def get_universes(self) -> list[UniverseSummary]:
        """Retrieves all universes with a summary"""
        universes = db_manager.get_all("universes", order_by="name")

        # Add the number of characters for each universe
        for universe in universes:
            query = "SELECT COUNT(*) as count FROM characters WHERE universe_id = ?"
            result = db_manager.execute_query(query, (universe["id"],), fetchall=False)
            universe["character_count"] = result["count"] if result else 0

        return [UniverseSummary(**universe) for universe in universes]

    def get_universe_details(self, universe_id: int) -> Optional[UniverseDetail]:
        """Retrieves the complete details of a universe with its elements and characters"""
        universe = self.get_universe(universe_id)
        if not universe:
            return None

        # Retrieve the universe elements
        query = "SELECT * FROM universe_elements WHERE universe_id = ? ORDER BY importance DESC, name ASC"
        elements = db_manager.execute_query(query, (universe_id,))
        universe_elements = [UniverseElement(**element) for element in elements]

        # Retrieve the characters associated with this universe
        query = "SELECT id, name, description FROM characters WHERE universe_id = ? ORDER BY name ASC"
        characters = db_manager.execute_query(query, (universe_id,))

        return UniverseDetail(
            **universe.model_dump(), elements=universe_elements, characters=characters
        )

    def update_universe(self, universe_id: int, updates: dict[str, Any]) -> bool:
        """Updates a universe"""
        rows_updated = db_manager.update("universes", updates, "id = ?", (universe_id,))
        return rows_updated > 0

    def delete_universe(self, universe_id: int) -> bool:
        """Deletes a universe"""
        # Check if any characters are associated with this universe
        query = "SELECT COUNT(*) as count FROM characters WHERE universe_id = ?"
        result = db_manager.execute_query(query, (universe_id,), fetchall=False)

        if result and result["count"] > 0:
            # Update the characters to remove the reference to the universe
            db_manager.update(
                "characters", {"universe_id": None}, "universe_id = ?", (universe_id,)
            )

        # Delete the universe elements
        db_manager.delete("universe_elements", "universe_id = ?", (universe_id,))

        # Delete the universe
        rows_deleted = db_manager.delete("universes", "id = ?", (universe_id,))
        return rows_deleted > 0

    def add_universe_element(self, element: UniverseElementCreate) -> int:
        """Adds an element to a universe"""
        element_dict = element.model_dump()
        element_id = db_manager.insert("universe_elements", element_dict)
        return element_id

    def get_universe_element(self, element_id: int) -> Optional[UniverseElement]:
        """Retrieves a universe element by its ID"""
        element = db_manager.get_by_id("universe_elements", element_id)
        if element:
            return UniverseElement(**element)
        return None

    def get_universe_elements(self, universe_id: int) -> list[UniverseElement]:
        """Retrieves all elements of a universe"""
        query = "SELECT * FROM universe_elements WHERE universe_id = ? ORDER BY importance DESC, name ASC"
        elements = db_manager.execute_query(query, (universe_id,))
        return [UniverseElement(**element) for element in elements]

    def update_universe_element(self, element_id: int, updates: dict[str, Any]) -> bool:
        """Updates a universe element"""
        rows_updated = db_manager.update(
            "universe_elements", updates, "id = ?", (element_id,)
        )
        return rows_updated > 0

    def delete_universe_element(self, element_id: int) -> bool:
        """Deletes a universe element"""
        rows_deleted = db_manager.delete("universe_elements", "id = ?", (element_id,))
        return rows_deleted > 0

    def get_universe_description(self, universe_id: int) -> str:
        """Generates a complete description of the universe with its elements"""
        universe = self.get_universe(universe_id)
        if not universe:
            return ""

        elements = self.get_universe_elements(universe_id)

        description = f"Universe name: {universe.name}\n"
        description += f"Description: {universe.description}\n"

        if universe.time_period:
            description += f"Period: {universe.time_period}\n"

        if universe.rules:
            description += f"Rules: {universe.rules}\n"

        if elements:
            description += "\nImportant elements of this universe:\n"

            # Sort by element type
            elements_by_type = {}
            for element in elements:
                if element.type not in elements_by_type:
                    elements_by_type[element.type] = []
                elements_by_type[element.type].append(element)

            for element_type, type_elements in elements_by_type.items():
                description += f"\n{element_type.capitalize()}s:\n"
                for element in type_elements:
                    description += f"- {element.name}: {element.description}\n"

        return description


# Global instance of the universe manager
universe_manager = UniverseManager()
