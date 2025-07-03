"""
Gestionnaire des univers et leurs éléments
"""

import logging
from typing import Any, Dict, List, Optional

from backend.models.universe import (
    Universe,
    UniverseCreate,
    UniverseDetail,
    UniverseElement,
    UniverseElementCreate,
    UniverseSummary,
)
from backend.utils.db import db_manager

logger = logging.getLogger(__name__)


class UniverseManager:
    """Gestionnaire des univers"""

    def create_universe(self, universe: UniverseCreate) -> int:
        """Crée un nouvel univers"""
        universe_dict = universe.dict()
        universe_id = db_manager.insert("universes", universe_dict)
        logger.info(f"Univers créé: {universe.name} (ID: {universe_id})")
        return universe_id

    def get_universe(self, universe_id: int) -> Optional[Universe]:
        """Récupère un univers par son ID"""
        universe = db_manager.get_by_id("universes", universe_id)
        if universe:
            return Universe(**universe)
        return None

    def get_universes(self) -> List[UniverseSummary]:
        """Récupère tous les univers avec un résumé"""
        universes = db_manager.get_all("universes", order_by="name")

        # Ajouter le nombre de personnages pour chaque univers
        for universe in universes:
            query = "SELECT COUNT(*) as count FROM characters WHERE universe_id = ?"
            result = db_manager.execute_query(
                query, (universe["id"],), fetchall=False)
            universe["character_count"] = result["count"] if result else 0

        return [UniverseSummary(**universe) for universe in universes]

    def get_universe_details(self, universe_id: int) -> Optional[UniverseDetail]:
        """Récupère les détails complets d'un univers avec ses éléments et personnages"""
        universe = self.get_universe(universe_id)
        if not universe:
            return None

        # Récupérer les éléments de l'univers
        query = "SELECT * FROM universe_elements WHERE universe_id = ? ORDER BY importance DESC, name ASC"
        elements = db_manager.execute_query(query, (universe_id,))
        universe_elements = [UniverseElement(
            **element) for element in elements]

        # Récupérer les personnages associés à cet univers
        query = "SELECT id, name, description FROM characters WHERE universe_id = ? ORDER BY name ASC"
        characters = db_manager.execute_query(query, (universe_id,))

        return UniverseDetail(
            **universe.dict(),
            elements=universe_elements,
            characters=characters
        )

    def update_universe(self, universe_id: int, updates: Dict[str, Any]) -> bool:
        """Met à jour un univers"""
        rows_updated = db_manager.update(
            "universes", updates, "id = ?", (universe_id,))
        return rows_updated > 0

    def delete_universe(self, universe_id: int) -> bool:
        """Supprime un univers"""
        # Vérifier si des personnages sont associés à cet univers
        query = "SELECT COUNT(*) as count FROM characters WHERE universe_id = ?"
        result = db_manager.execute_query(
            query, (universe_id,), fetchall=False)

        if result and result["count"] > 0:
            # Mettre à jour les personnages pour supprimer la référence à l'univers
            db_manager.update(
                "characters",
                {"universe_id": None},
                "universe_id = ?",
                (universe_id,)
            )

        # Supprimer les éléments de l'univers
        db_manager.delete("universe_elements",
                          "universe_id = ?", (universe_id,))

        # Supprimer l'univers
        rows_deleted = db_manager.delete("universes", "id = ?", (universe_id,))
        return rows_deleted > 0

    def add_universe_element(self, element: UniverseElementCreate) -> int:
        """Ajoute un élément à un univers"""
        element_dict = element.dict()
        element_id = db_manager.insert("universe_elements", element_dict)
        return element_id

    def get_universe_element(self, element_id: int) -> Optional[UniverseElement]:
        """Récupère un élément d'univers par son ID"""
        element = db_manager.get_by_id("universe_elements", element_id)
        if element:
            return UniverseElement(**element)
        return None

    def get_universe_elements(self, universe_id: int) -> List[UniverseElement]:
        """Récupère tous les éléments d'un univers"""
        query = "SELECT * FROM universe_elements WHERE universe_id = ? ORDER BY importance DESC, name ASC"
        elements = db_manager.execute_query(query, (universe_id,))
        return [UniverseElement(**element) for element in elements]

    def update_universe_element(self, element_id: int, updates: Dict[str, Any]) -> bool:
        """Met à jour un élément d'univers"""
        rows_updated = db_manager.update(
            "universe_elements", updates, "id = ?", (element_id,))
        return rows_updated > 0

    def delete_universe_element(self, element_id: int) -> bool:
        """Supprime un élément d'univers"""
        rows_deleted = db_manager.delete(
            "universe_elements", "id = ?", (element_id,))
        return rows_deleted > 0

    def get_universe_description(self, universe_id: int) -> str:
        """Génère une description complète de l'univers avec ses éléments"""
        universe = self.get_universe(universe_id)
        if not universe:
            return ""

        elements = self.get_universe_elements(universe_id)

        description = f"Nom de l'univers: {universe.name}\n"
        description += f"Description: {universe.description}\n"

        if universe.time_period:
            description += f"Période: {universe.time_period}\n"

        if universe.rules:
            description += f"Règles: {universe.rules}\n"

        if elements:
            description += "\nÉléments importants de cet univers:\n"

            # Trier par type d'élément
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


# Instance globale du gestionnaire d'univers
universe_manager = UniverseManager()
