"""
Service de gestion des personnages
"""

import logging
import datetime
import json
from typing import List, Dict, Any, Optional, Tuple

from utils.db import db_manager
from models.character import Character, CharacterCreate, CharacterSummary, CharacterState
from models.character import CharacterTrait, PersonalityTraits, TraitChange
from models.relationship import Relationship, RelationshipCreate, UserCharacterRelationship
from .memory_manager import memory_manager

logger = logging.getLogger(__name__)


class CharacterManager:
    """Gestionnaire de personnages"""

    # Définition des traits par défaut pour les nouveaux personnages
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

    def create_character(self, character: CharacterCreate) -> int:
        """Crée un nouveau personnage"""
        character_dict = character.dict(exclude={"initial_traits"})
        character_dict["created_at"] = datetime.datetime.now()

        # Vérification de l'existence de l'univers si universe_id est fourni
        if character_dict.get("universe_id"):
            universe = db_manager.get_by_id(
                "universes", character_dict["universe_id"])
            if not universe:
                logger.warning(
                    f"L'univers avec l'ID {character_dict['universe_id']} n'existe pas. Ce champ sera défini à NULL.")
                # Définir à NULL si l'univers n'existe pas
                character_dict["universe_id"] = None

        character_id = db_manager.insert("characters", character_dict)
        logger.info(f"Personnage créé: {character.name} (ID: {character_id})")

        # Initialiser une relation avec l'utilisateur
        self._initialize_user_relationship(character_id)

        # Initialiser les traits de personnalité
        if character.initial_traits:
            self._initialize_personality_traits(
                character_id, character.initial_traits)
        else:
            # Utiliser les traits par défaut
            self._initialize_personality_traits(
                character_id, self.DEFAULT_TRAITS)

        return character_id

    def _initialize_user_relationship(self, character_id: int) -> int:
        """Initialise une relation entre le personnage et l'utilisateur"""
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

    def _initialize_personality_traits(self, character_id: int, initial_traits: List[Dict[str, Any]]) -> None:
        """Initialise les traits de personnalité d'un personnage"""
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

    def get_character(self, character_id: int) -> Optional[Character]:
        """Récupère un personnage par son ID"""
        character = db_manager.get_by_id("characters", character_id)
        if character:
            # Ajouter le nom de l'univers si disponible
            if character.get("universe_id"):
                universe = db_manager.get_by_id(
                    "universes", character["universe_id"])
                if universe:
                    character["universe"] = universe["name"]

            return Character(**character)
        return None

    def get_characters(self, limit: int = None) -> List[CharacterSummary]:
        """Récupère tous les personnages"""
        characters = db_manager.get_all(
            "characters", order_by="name", limit=limit)

        # Ajouter les noms d'univers
        universe_ids = [c["universe_id"]
                        for c in characters if c["universe_id"]]
        universes = {}

        if universe_ids:
            query = f"SELECT id, name FROM universes WHERE id IN ({','.join('?' for _ in universe_ids)})"
            results = db_manager.execute_query(query, tuple(universe_ids))
            universes = {u["id"]: u["name"] for u in results}

        # Ajouter le nom de l'univers à chaque personnage
        for character in characters:
            if character["universe_id"] and character["universe_id"] in universes:
                character["universe"] = universes[character["universe_id"]]

        return [CharacterSummary(**character) for character in characters]

    def update_character(self, character_id: int, updates: Dict[str, Any]) -> bool:
        """Met à jour un personnage"""
        rows_updated = db_manager.update(
            "characters", updates, "id = ?", (character_id,))
        return rows_updated > 0

    def delete_character(self, character_id: int) -> bool:
        """Supprime un personnage"""
        # Récupérer toutes les mémoires du personnage
        memories = memory_manager.get_memories(character_id)

        # Supprimer les mémoires une par une (pour s'assurer que les faits sont aussi supprimés)
        for memory in memories:
            memory_manager.delete_memory(memory.id)

        # Supprimer les relations
        db_manager.delete("relationships", "character_id = ?", (character_id,))

        # Supprimer les traits de personnalité
        db_manager.delete("personality_traits",
                          "character_id = ?", (character_id,))

        # Supprimer l'historique des changements de traits
        db_manager.delete("trait_changes", "character_id = ?", (character_id,))

        # Supprimer le personnage
        rows_deleted = db_manager.delete(
            "characters", "id = ?", (character_id,))
        return rows_deleted > 0

    def get_character_state(self, character_id: int) -> CharacterState:
        """Récupère l'état actuel d'un personnage"""
        character = self.get_character(character_id)
        if not character:
            raise ValueError(f"Personnage introuvable (ID: {character_id})")

        # Récupérer la relation avec l'utilisateur
        query = "SELECT * FROM relationships WHERE character_id = ? AND target_name = 'user'"
        relationships = db_manager.execute_query(
            query, (character_id,), fetchall=True)

        relationship = relationships[0] if relationships else {
            "sentiment": 0.0,
            "trust": 0.0,
            "familiarity": 0.0
        }

        # Récupérer les mémoires récentes
        recent_memories = memory_manager.get_memories(character_id, limit=10)
        recent_memories_dict = [memory.dict() for memory in recent_memories]

        # Récupérer les traits actifs
        active_traits = self.get_personality_traits_as_dict(character_id)

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
        """Détermine l'humeur du personnage en fonction de sa relation, ses mémoires récentes et ses traits de personnalité"""
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

    def update_relationship(self, character_id: int, target_name: str, updates: Dict[str, Any]) -> bool:
        """Met à jour une relation"""
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

    def get_personality_traits(self, character_id: int) -> PersonalityTraits:
        """Récupère les traits de personnalité d'un personnage"""
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
        """Récupère les traits de personnalité d'un personnage sous forme de dictionnaire {nom: valeur}"""
        query = "SELECT name, value FROM personality_traits WHERE character_id = ?"
        traits_data = db_manager.execute_query(query, (character_id,))

        return {trait["name"]: trait["value"] for trait in traits_data}

    def get_trait_history(self, character_id: int, trait_name: str = None) -> List[TraitChange]:
        """Récupère l'historique des changements de traits d'un personnage"""
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
        """Met à jour la valeur d'un trait de personnalité et enregistre le changement"""
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
        Analyse l'interaction et met à jour les traits de personnalité en fonction du contenu

        Args:
            character_id: ID du personnage
            interaction_text: Texte de l'interaction (message utilisateur ou réponse du personnage)
            intensity: Intensité de l'effet (entre 0.0 et 1.0)

        Returns:
            Liste des traits modifiés avec leurs anciennes et nouvelles valeurs
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


# Instance globale du gestionnaire de personnages
character_manager = CharacterManager()
