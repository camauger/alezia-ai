"""
Service de gestion des personnages
"""

import logging
import datetime
from typing import List, Dict, Any, Optional

from utils.db import db_manager
from models.character import Character, CharacterCreate, CharacterSummary, CharacterState
from models.relationship import Relationship, RelationshipCreate, UserCharacterRelationship
from .memory_manager import memory_manager

logger = logging.getLogger(__name__)


class CharacterManager:
    """Gestionnaire de personnages"""

    def create_character(self, character: CharacterCreate) -> int:
        """Crée un nouveau personnage"""
        character_dict = character.dict()
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

        # Déterminer l'humeur en fonction des mémoires et relations récentes
        mood = self._determine_mood(relationship, recent_memories_dict)

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
            }
        )

    def _determine_mood(self, relationship: Dict[str, Any], recent_memories: List[Dict[str, Any]]) -> str:
        """Détermine l'humeur du personnage en fonction de sa relation et ses mémoires récentes"""
        # Logique simple basée sur le sentiment de la relation avec l'utilisateur
        sentiment = relationship.get("sentiment", 0.0)

        if sentiment > 0.7:
            return "cheerful"
        elif sentiment > 0.3:
            return "friendly"
        elif sentiment > -0.3:
            return "neutral"
        elif sentiment > -0.7:
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

    def get_relationships(self, character_id: int) -> List[Relationship]:
        """Récupère toutes les relations d'un personnage"""
        query = "SELECT * FROM relationships WHERE character_id = ? ORDER BY last_updated DESC"
        relationships = db_manager.execute_query(query, (character_id,))
        return [Relationship(**relationship) for relationship in relationships]

    def get_user_relationship(self, character_id: int) -> UserCharacterRelationship:
        """Récupère la relation entre l'utilisateur et un personnage"""
        query = "SELECT * FROM relationships WHERE character_id = ? AND target_name = 'user'"
        relationships = db_manager.execute_query(
            query, (character_id,), fetchall=True)

        if relationships:
            relationship = relationships[0]
            return UserCharacterRelationship(
                character_id=character_id,
                username="user",
                sentiment=relationship.get("sentiment", 0.0),
                trust=relationship.get("trust", 0.0),
                familiarity=relationship.get("familiarity", 0.0),
                interactions_count=0,  # À calculer si nécessaire
                notes=relationship.get("notes")
            )
        else:
            # Créer une relation par défaut
            self._initialize_user_relationship(character_id)
            return UserCharacterRelationship(character_id=character_id)

    def get_character_profile(self, character_id: int) -> str:
        """
        Génère un profil complet du personnage pour être utilisé comme contexte dans les conversations.
        Inclut tous les paramètres importants du personnage et les faits extraits des mémoires.

        Args:
            character_id: ID du personnage

        Returns:
            Profil complet formaté sous forme de texte
        """
        from services.memory_manager import memory_manager

        try:
            character = self.get_character(character_id)
            if not character:
                return "Personnage inconnu."

            # Récupérer les faits les plus importants sur le personnage
            facts = memory_manager.get_facts(character_id)

            # Organiser les faits par sujet
            facts_by_subject = {}
            for fact in facts:
                if fact.subject not in facts_by_subject:
                    facts_by_subject[fact.subject] = []
                facts_by_subject[fact.subject].append(fact)

            # Construire le profil
            profile = f"# PROFIL DE PERSONNAGE: {character.name.upper()}\n\n"

            # Informations de base
            profile += "## Informations de base\n"
            profile += f"Nom: {character.name}\n"
            profile += f"Description: {character.description}\n\n"

            # Personnalité
            profile += "## Personnalité et comportement\n"
            profile += f"{character.personality}\n\n"

            # Histoire
            profile += "## Histoire et contexte\n"
            profile += f"{character.backstory}\n\n"

            # Faits connus
            if facts:
                profile += "## Faits connus sur le personnage\n"

                for subject, subject_facts in facts_by_subject.items():
                    # Trier les faits par confiance (décroissante)
                    subject_facts.sort(
                        key=lambda x: x.confidence, reverse=True)

                    profile += f"### À propos de {subject}\n"
                    for fact in subject_facts:
                        # N'inclure que les faits avec une confiance minimale
                        if fact.confidence >= 0.5:
                            confidence_indicator = "!" if fact.confidence >= 0.8 else ""
                            profile += f"- {confidence_indicator}{fact.predicate} {fact.object}{confidence_indicator}\n"
                    profile += "\n"

            # Instructions supplémentaires pour le comportement en conversation
            profile += "## Instructions pour la conversation\n"
            profile += "- Reste fidèle à la personnalité décrite ci-dessus.\n"
            profile += "- Utilise les faits connus pour contextualiser les réponses.\n"
            profile += "- Les faits marqués avec '!' sont particulièrement importants et certains.\n"
            profile += "- Maintiens la cohérence avec l'histoire du personnage.\n"
            profile += f"- Ce personnage appartient à l'univers: '{character.universe.name}'.\n"

            return profile

        except Exception as e:
            logger.error(
                f"Erreur lors de la génération du profil du personnage {character_id}: {e}")
            return "Erreur lors de la génération du profil du personnage."

    def get_character_conversation_context(self, character_id: int, include_memories: bool = True) -> Dict[str, Any]:
        """
        Prépare le contexte complet pour une conversation avec un personnage.

        Args:
            character_id: ID du personnage
            include_memories: Si True, inclut les mémoires pertinentes

        Returns:
            Dictionnaire avec toutes les informations nécessaires pour le contexte
        """
        from services.memory_manager import memory_manager

        character = self.get_character(character_id)
        if not character:
            return {"error": "Personnage introuvable"}

        context = {
            "character": character.dict(),
            "profile": self.get_character_profile(character_id),
            "memories": []
        }

        # Ajouter les mémoires les plus importantes
        if include_memories:
            try:
                # Récupérer les mémoires importantes pour le contexte de la conversation
                important_memories = memory_manager.get_memories(
                    character_id,
                    limit=10
                )

                # Trier par importance décroissante
                important_memories.sort(
                    key=lambda x: x.importance, reverse=True)

                # Inclure seulement les 5 plus importantes pour ne pas surcharger le contexte
                context["memories"] = important_memories[:5]

            except Exception as e:
                logger.error(
                    f"Erreur lors de la récupération des mémoires pour le contexte: {e}")

        return context


# Instance globale du gestionnaire de personnages
character_manager = CharacterManager()
