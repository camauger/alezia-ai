"""
Service for managing personality traits and their evolution.
"""
import logging
import datetime
from typing import List, Dict, Any

from backend.utils.db import db_manager
from backend.models.character import CharacterTrait, PersonalityTraits, TraitChange

logger = logging.getLogger(__name__)

class PersonalityService:
    """Service for managing personality traits"""

    DEFAULT_TRAITS = [
        {
            "name": "extraversion",
            "value": 0.0,
            "category": "social",
            "description": "Tendance à rechercher la stimulation dans le monde extérieur",
            "volatility": 0.2
        },
        {
            "name": "agréabilité",
            "value": 0.0,
            "category": "social",
            "description": "Tendance à être compatissant et coopératif envers les autres",
            "volatility": 0.3
        },
        {
            "name": "conscienciosité",
            "value": 0.0,
            "category": "comportemental",
            "description": "Tendance à être organisé et à penser aux conséquences",
            "volatility": 0.1
        },
        {
            "name": "stabilité émotionnelle",
            "value": 0.0,
            "category": "émotionnel",
            "description": "Tendance à rester calme face au stress",
            "volatility": 0.4
        },
        {
            "name": "ouverture",
            "value": 0.0,
            "category": "cognitif",
            "description": "Tendance à être ouvert aux nouvelles expériences",
            "volatility": 0.3
        },
        {
            "name": "curiosité",
            "value": 0.3,
            "category": "cognitif",
            "description": "Tendance à vouloir explorer et apprendre",
            "volatility": 0.4
        },
        {
            "name": "impulsivité",
            "value": 0.0,
            "category": "comportemental",
            "description": "Tendance à agir sans réfléchir",
            "volatility": 0.5
        }
    ]

    def initialize_personality_traits(self, character_id: int, initial_traits: List[Dict[str, Any]]) -> None:
        """Initializes the personality traits of a character"""
        now = datetime.datetime.now().isoformat()
        traits_inserted = 0

        for trait_data in initial_traits:
            trait = {
                "character_id": character_id,
                "name": trait_data["name"],
                "value": trait_data["value"],
                "category": trait_data["category"],
                "description": trait_data["description"],
                "volatility": trait_data.get("volatility", 0.2),
                "last_updated": now
            }

            trait_id = db_manager.insert("personality_traits", trait)
            traits_inserted += 1

            # Enregistrer l'initialisation comme premier changement
            change = {
                "character_id": character_id,
                "trait_id": trait_id,
                "old_value": 0.0,  # Valeur initiale supposée
                "new_value": trait_data["value"],
                "change_amount": trait_data["value"],
                "reason": "Initialisation du trait",
                "timestamp": now
            }

            db_manager.insert("trait_changes", change)

        logger.info(
            f"Initialisé {traits_inserted} traits pour le personnage ID {character_id}")

    def get_personality_traits(self, character_id: int) -> PersonalityTraits:
        """Retrieves the personality traits of a character"""
        query = "SELECT * FROM personality_traits WHERE character_id = ?"
        traits_data = db_manager.execute_query(query, (character_id,))

        if not traits_data:
            # Renvoyer un objet vide si le personnage n'a pas de traits
            return PersonalityTraits(traits=[], last_updated=datetime.datetime.now())

        # Convertir les données en objets CharacterTrait
        trait_objects = []
        for trait in traits_data:
            trait_obj = CharacterTrait(
                name=trait["name"],
                value=trait["value"],
                category=trait["category"],
                description=trait["description"],
                volatility=trait["volatility"]
            )
            trait_objects.append(trait_obj)

        # Trouver la date de dernière mise à jour (la plus récente parmi tous les traits)
        last_updated_dates = []
        for t in traits_data:
            if t.get("last_updated"):
                # Gérer les différents types possibles de last_updated
                if isinstance(t["last_updated"], str):
                    last_updated_dates.append(
                        datetime.datetime.fromisoformat(t["last_updated"]))
                elif isinstance(t["last_updated"], datetime.datetime):
                    last_updated_dates.append(t["last_updated"])

        # Utiliser la date actuelle si aucune date valide n'est trouvée
        if last_updated_dates:
            last_updated = max(last_updated_dates)
        else:
            last_updated = datetime.datetime.now()

        return PersonalityTraits(traits=trait_objects, last_updated=last_updated)

    def get_personality_traits_as_dict(self, character_id: int) -> Dict[str, float]:
        """Retrieves the personality traits of a character as a dictionary {name: value}"""
        query = "SELECT name, value FROM personality_traits WHERE character_id = ?"
        traits_data = db_manager.execute_query(query, (character_id,))

        return {trait["name"]: trait["value"] for trait in traits_data}

    def get_trait_history(self, character_id: int, trait_name: str = None) -> List[TraitChange]:
        """Retrieves the history of trait changes for a character"""
        if trait_name:
            # Trouver d'abord l'ID du trait
            query = "SELECT id FROM personality_traits WHERE character_id = ? AND name = ?"
            trait_data = db_manager.execute_query(
                query, (character_id, trait_name), fetchall=False)

            if not trait_data:
                return []

            trait_id = trait_data["id"]

            # Récupérer l'historique pour ce trait spécifique
            query = """
            SELECT tc.*, pt.name as trait_name
            FROM trait_changes tc
            JOIN personality_traits pt ON tc.trait_id = pt.id
            WHERE tc.character_id = ? AND tc.trait_id = ?
            ORDER BY tc.timestamp DESC
            """
            changes_data = db_manager.execute_query(
                query, (character_id, trait_id))
        else:
            # Récupérer l'historique pour tous les traits
            query = """
            SELECT tc.*, pt.name as trait_name
            FROM trait_changes tc
            JOIN personality_traits pt ON tc.trait_id = pt.id
            WHERE tc.character_id = ?
            ORDER BY tc.timestamp DESC
            """
            changes_data = db_manager.execute_query(query, (character_id,))

        # Convertir les données en objets TraitChange
        changes = []
        for change in changes_data:
            # Gérer les différents types de timestamp possibles
            timestamp = change["timestamp"]
            if isinstance(timestamp, str):
                timestamp = datetime.datetime.fromisoformat(timestamp)
            elif not isinstance(timestamp, datetime.datetime):
                # Si le timestamp n'est ni une chaîne ni un datetime, utiliser l'heure actuelle
                timestamp = datetime.datetime.now()

            change_obj = TraitChange(
                trait_name=change["trait_name"],
                old_value=change["old_value"],
                new_value=change["new_value"],
                change_amount=change["change_amount"],
                reason=change["reason"],
                timestamp=timestamp
            )
            changes.append(change_obj)

        return changes

    def update_trait(self, character_id: int, trait_name: str, new_value: float, reason: str) -> bool:
        """Updates the value of a personality trait and records the change"""
        # Récupérer le trait actuel
        query = "SELECT * FROM personality_traits WHERE character_id = ? AND name = ?"
        trait = db_manager.execute_query(
            query, (character_id, trait_name), fetchall=False)

        if not trait:
            logger.warning(
                f"Trait {trait_name} introuvable pour le personnage ID {character_id}")
            return False

        # S'assurer que la nouvelle valeur est dans les limites
        new_value = max(-1.0, min(1.0, new_value))

        # Si la valeur n'a pas changé, ne rien faire
        if trait["value"] == new_value:
            return True

        # Mettre à jour le trait
        now = datetime.datetime.now().isoformat()
        updates = {
            "value": new_value,
            "last_updated": now
        }

        updated = db_manager.update(
            "personality_traits",
            updates,
            "id = ?",
            (trait["id"],)
        ) > 0

        if updated:
            # Enregistrer le changement
            change = {
                "character_id": character_id,
                "trait_id": trait["id"],
                "old_value": trait["value"],
                "new_value": new_value,
                "change_amount": new_value - trait["value"],
                "reason": reason,
                "timestamp": now
            }

            db_manager.insert("trait_changes", change)
            logger.info(
                f"Trait {trait_name} mis à jour pour le personnage ID {character_id}: {trait['value']} → {new_value}")

        return updated

    def update_traits_from_interaction(self, character_id: int, interaction_text: str, intensity: float = 1.0) -> List[Dict[str, Any]]:
        """
        Analyzes the interaction and updates personality traits based on the content.
        """
        # Obtenir les traits actuels
        traits = self.get_personality_traits(character_id)
        if not traits.traits:
            logger.warning(
                f"Aucun trait trouvé pour le personnage ID {character_id}")
            return []

        # Analyser le texte pour détecter les marqueurs qui peuvent influencer les traits
        text_lower = interaction_text.lower()

        trait_changes = []

        # 1. Extraversion - Influencée par expressions sociales vs introspectives
        social_markers = ["ensemble", "groupe", "amis",
                          "rencontrer", "parler", "sortir", "fête", "partager"]
        introspective_markers = [
            "seul", "réfléchir", "méditer", "calme", "tranquille", "isolé", "intime"]

        social_score = sum(text_lower.count(marker)
                           for marker in social_markers) * 0.05
        introspective_score = sum(text_lower.count(marker)
                                  for marker in introspective_markers) * 0.05
        extraversion_change = (social_score - introspective_score) * intensity

        # 2. Agréabilité - Influencée par expressions d'empathie vs antagonisme
        empathy_markers = ["comprendre", "aider", "soutenir",
                           "gentil", "sympathie", "merci", "apprécier"]
        antagonistic_markers = ["colère", "détester",
                                "frustré", "agacé", "énervé", "idiot", "stupide"]

        empathy_score = sum(text_lower.count(marker)
                            for marker in empathy_markers) * 0.05
        antagonistic_score = sum(text_lower.count(marker)
                                 for marker in antagonistic_markers) * 0.05
        agreeableness_change = (empathy_score - antagonistic_score) * intensity

        # 3. Curiosité - Influencée par expressions de curiosité
        curiosity_markers = ["pourquoi", "comment", "intéressant",
                             "apprendre", "découvrir", "question", "curieux"]
        curious_score = sum(text_lower.count(marker)
                            for marker in curiosity_markers) * 0.08
        curiosity_change = curious_score * intensity

        # 4. Impulsivité - Influencée par expressions impulsives vs réfléchies
        impulsive_markers = ["immédiatement", "tout de suite",
                             "maintenant", "spontané", "sans réfléchir"]
        thoughtful_markers = ["réfléchir", "considérer",
                              "planifier", "attendre", "patient"]

        impulsive_score = sum(text_lower.count(marker)
                              for marker in impulsive_markers) * 0.06
        thoughtful_score = sum(text_lower.count(marker)
                               for marker in thoughtful_markers) * 0.06
        impulsivity_change = (impulsive_score - thoughtful_score) * intensity

        # Appliquer les changements détectés
        changes_to_apply = [
            {"name": "extraversion", "change": extraversion_change,
                "reason": "Interaction sociale"},
            {"name": "agréabilité", "change": agreeableness_change,
                "reason": "Expression empathique/antagoniste"},
            {"name": "curiosité", "change": curiosity_change,
                "reason": "Expression de curiosité"},
            {"name": "impulsivité", "change": impulsivity_change,
                "reason": "Expression d'impulsivité/réflexion"}
        ]

        for change_info in changes_to_apply:
            trait_name = change_info["name"]
            change_amount = change_info["change"]
            reason = change_info["reason"]

            # Si le changement est trop petit, ignorer
            if abs(change_amount) < 0.01:
                continue

            # Trouver le trait correspondant
            trait_value = traits.get_trait_value(trait_name)

            # La volatilité détermine la rapidité avec laquelle un trait peut changer
            trait_obj = next(
                (t for t in traits.traits if t.name.lower() == trait_name.lower()), None)
            volatility = trait_obj.volatility if trait_obj else 0.2

            # Appliquer le changement en tenant compte de la volatilité
            new_value = trait_value + (change_amount * volatility)

            # Mettre à jour le trait
            if self.update_trait(character_id, trait_name, new_value, reason):
                trait_changes.append({
                    "trait_name": trait_name,
                    "old_value": trait_value,
                    "new_value": new_value,
                    "change": change_amount,
                    "reason": reason
                })

        return trait_changes

personality_service = PersonalityService()