"""
Service de gestion des sessions de chat
"""

import logging
import json
import datetime
from typing import List, Dict, Any, Optional, Tuple
import asyncio

from utils.db import db_manager
from models.memory import MemoryCreate
from .llm_service import llm_service
from .memory_manager import memory_manager
from .character_manager import character_manager
from .universe_manager import universe_manager

logger = logging.getLogger(__name__)


class ChatManager:
    """Gestionnaire des sessions de chat"""

    def create_session(self, character_id: int) -> Dict[str, Any]:
        """Crée une nouvelle session de chat"""
        session_data = {
            "character_id": character_id,
            "start_time": datetime.datetime.now(),
            "end_time": None,
            "summary": None
        }

        session_id = db_manager.insert("sessions", session_data)
        logger.info(
            f"Session créée pour le personnage {character_id} (ID: {session_id})")

        return {
            "id": session_id,
            "character_id": character_id,
            "start_time": session_data["start_time"],
            "messages": []
        }

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Récupère une session de chat par son ID"""
        session = db_manager.get_by_id("sessions", session_id)
        if not session:
            return None

        # Récupérer les messages de la session
        query = "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC"
        messages = db_manager.execute_query(query, (session_id,))

        session["messages"] = messages
        return session

    def get_character_sessions(self, character_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupère les sessions de chat pour un personnage"""
        query = "SELECT * FROM sessions WHERE character_id = ? ORDER BY start_time DESC LIMIT ?"
        sessions = db_manager.execute_query(query, (character_id, limit))
        return sessions

    async def send_message(self, session_id: int, content: str, is_user: bool = True) -> Dict[str, Any]:
        """Envoie un message dans une session et génère une réponse si nécessaire"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session introuvable (ID: {session_id})")

        character_id = session["character_id"]

        # Enregistrer le message
        message_data = {
            "session_id": session_id,
            "is_user": is_user,
            "content": content,
            "timestamp": datetime.datetime.now(),
            "metadata": {}
        }

        message_id = db_manager.insert("messages", message_data)
        logger.info(f"Message enregistré (ID: {message_id})")

        # Si c'est un message utilisateur, générer une réponse
        if is_user:
            # Stocker le message comme mémoire
            self._store_message_as_memory(character_id, content, is_user=True)

            # Générer une réponse
            response = await self._generate_response(session_id, character_id, content)

            if "error" not in response:
                # Stocker la réponse comme mémoire
                self._store_message_as_memory(
                    character_id, response["content"], is_user=False)

            return response

        return {
            "id": message_id,
            "content": content,
            "timestamp": message_data["timestamp"].isoformat()
        }

    async def _generate_response(self, session_id: int, character_id: int, user_message: str) -> Dict[str, Any]:
        """Génère une réponse du personnage"""
        # Récupérer le personnage
        character = character_manager.get_character(character_id)
        if not character:
            return {"content": "Erreur: Personnage introuvable", "error": "character_not_found"}

        # Récupérer l'univers si disponible
        universe_description = None
        if character.universe_id:
            universe = universe_manager.get_universe(character.universe_id)
            if universe:
                universe_description = universe_manager.get_universe_description(
                    universe.id)

        # Récupérer l'état du personnage
        character_state = character_manager.get_character_state(character_id)

        # Récupérer les mémoires pertinentes
        relevant_memories = memory_manager.get_relevant_memories(
            character_id, user_message, limit=5)
        memory_context = ""
        if relevant_memories:
            memory_context = "Voici quelques souvenirs pertinents pour cette conversation:\n"
            for i, memory in enumerate(relevant_memories):
                memory_context += f"{i+1}. {memory.content}\n"

        # Récupérer l'historique récent de la conversation
        query = "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT 10"
        recent_messages = db_manager.execute_query(query, (session_id,))
        recent_messages.reverse()  # Pour avoir l'ordre chronologique

        conversation_history = ""
        for msg in recent_messages:
            prefix = "User: " if msg["is_user"] else f"{character.name}: "
            conversation_history += f"{prefix}{msg['content']}\n"

        # Créer le prompt système
        system_prompt = await llm_service.create_character_system_prompt(
            character.name,
            character.description,
            character.personality,
            character.backstory,
            universe_description
        )

        if memory_context:
            system_prompt += f"\n\n{memory_context}"

        # Créer le prompt utilisateur
        prompt = conversation_history
        if not prompt:
            prompt = f"User: {user_message}\n{character.name}: "
        else:
            prompt += f"User: {user_message}\n{character.name}: "

        # Générer la réponse
        response = await llm_service.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            character_state=character_state
        )

        # Enregistrer la réponse comme message
        if "error" not in response:
            message_data = {
                "session_id": session_id,
                "is_user": False,
                "content": response["content"],
                "timestamp": datetime.datetime.now(),
                "metadata": {
                    "generation_time": response.get("generation_time"),
                    "tokens_used": response.get("tokens_used"),
                    "model": response.get("model")
                }
            }
            message_id = db_manager.insert("messages", message_data)
            response["id"] = message_id
            response["timestamp"] = message_data["timestamp"].isoformat()

        return response

    def _store_message_as_memory(self, character_id: int, content: str, is_user: bool) -> int:
        """Stocke un message comme mémoire pour le personnage"""
        memory_type = "user_message" if is_user else "character_message"
        importance = 1.0  # Importance de base

        memory = MemoryCreate(
            character_id=character_id,
            type=memory_type,
            content=content,
            importance=importance
        )

        memory_id = memory_manager.create_memory(memory)
        return memory_id

    def end_session(self, session_id: int) -> bool:
        """Termine une session de chat"""
        update_data = {
            "end_time": datetime.datetime.now()
        }
        rows_updated = db_manager.update(
            "sessions", update_data, "id = ?", (session_id,))

        if rows_updated > 0:
            # Optionnel: Générer un résumé de la session
            asyncio.create_task(self._generate_session_summary(session_id))

        return rows_updated > 0

    async def _generate_session_summary(self, session_id: int) -> None:
        """Génère un résumé de la session (en arrière-plan)"""
        try:
            session = self.get_session(session_id)
            if not session or not session.get("messages"):
                return

            # Extraire le contenu des messages
            messages_content = ""
            for msg in session["messages"]:
                prefix = "User" if msg["is_user"] else "Character"
                messages_content += f"{prefix}: {msg['content']}\n"

            # Créer un prompt pour générer le résumé
            prompt = f"Résume la conversation suivante en quelques phrases:\n\n{messages_content}\n\nRésumé:"

            # Générer le résumé
            response = await llm_service.generate_response(
                prompt=prompt,
                max_tokens=200
            )

            # Mettre à jour la session avec le résumé
            if "error" not in response:
                update_data = {
                    "summary": response["content"]
                }
                db_manager.update("sessions", update_data,
                                  "id = ?", (session_id,))
                logger.info(f"Résumé généré pour la session {session_id}")

        except Exception as e:
            logger.error(
                f"Erreur lors de la génération du résumé de session: {e}")


# Instance globale du gestionnaire de chat
chat_manager = ChatManager()
