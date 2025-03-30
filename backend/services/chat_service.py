"""
Service de gestion des sessions de chat et intégration LLM
"""

import logging
import uuid
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from services.llm_service import llm_service
from services.character_manager import CharacterManager
from services.memory_manager import MemoryManager
from utils.db import db_manager

logger = logging.getLogger(__name__)


class ChatService:
    """Service pour gérer les sessions de chat et l'intégration avec les LLM"""

    def __init__(self):
        """Initialise le service de chat"""
        self.sessions = {}  # Cache des sessions actives
        self.character_manager = CharacterManager()
        self.memory_manager = MemoryManager()

    def create_session(self, user_id: str, character_id: int, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Crée une nouvelle session de chat

        Args:
            user_id: ID de l'utilisateur
            character_id: ID du personnage
            context: Contexte de conversation optionnel

        Returns:
            Détails de la session créée
        """
        try:
            # Vérifier que le personnage existe
            character = self.character_manager.get_character(character_id)
            if not character:
                logger.error(f"Personnage {character_id} non trouvé")
                raise ValueError(f"Personnage {character_id} non trouvé")

            # Générer un ID de session unique
            session_id = str(uuid.uuid4())

            # Obtenir le contexte de conversation pour ce personnage
            if not context:
                context = self.character_manager.get_character_conversation_context(
                    character_id)

            # Créer l'objet session
            timestamp = datetime.now().isoformat()
            session = {
                "id": session_id,
                "user_id": user_id,
                "character_id": character_id,
                "created_at": timestamp,
                "updated_at": timestamp,
                "context": context,
                "active": True,
                "messages": []
            }

            # Stocker dans la base de données
            session_data = {
                "id": session_id,
                "user_id": user_id,
                "character_id": character_id,
                "created_at": timestamp,
                "updated_at": timestamp,
                "context": json.dumps(context),
                "active": 1
            }

            # Insérer en utilisant le gestionnaire de DB
            db_manager.insert("chat_sessions", session_data)

            # Mettre en cache
            self.sessions[session_id] = session

            return session

        except Exception as e:
            logger.error(f"Erreur lors de la création de session: {e}")
            raise

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une session

        Args:
            session_id: ID de la session

        Returns:
            Détails de la session
        """
        # Vérifier si en cache
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Sinon, récupérer depuis la base de données
        session = db_manager.get_by_id("chat_sessions", session_id)

        if not session:
            raise ValueError(f"Session {session_id} non trouvée")

        # Convertir le contexte JSON en dictionnaire
        if session.get("context"):
            session["context"] = json.loads(session["context"])

        # Mettre en cache
        self.sessions[session_id] = session

        return session

    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère la liste des sessions d'un utilisateur

        Args:
            user_id: ID de l'utilisateur
            limit: Nombre maximum de sessions à récupérer

        Returns:
            Liste des sessions
        """
        query = "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?"
        sessions = db_manager.execute_query(query, (user_id, limit))

        for session in sessions:
            if session.get("context"):
                session["context"] = json.loads(session["context"])

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Supprime une session de chat

        Args:
            session_id: ID de la session

        Returns:
            True si la suppression a réussi
        """
        try:
            # Supprimer les messages associés
            db_manager.delete("chat_messages", "session_id = ?", (session_id,))

            # Supprimer la session
            rows_deleted = db_manager.delete(
                "chat_sessions", "id = ?", (session_id,))

            # Supprimer du cache si présent
            if session_id in self.sessions:
                del self.sessions[session_id]

            return rows_deleted > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de session: {e}")
            return False

    def get_session_messages(self, session_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Récupère les messages d'une session

        Args:
            session_id: ID de la session
            limit: Nombre maximum de messages à récupérer
            offset: Décalage dans la liste des messages

        Returns:
            Liste des messages
        """
        query = """
        SELECT * FROM chat_messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
        LIMIT ? OFFSET ?
        """
        messages = db_manager.execute_query(query, (session_id, limit, offset))

        for message in messages:
            if message.get("metadata"):
                message["metadata"] = json.loads(message["metadata"])

        return messages

    def _build_conversation_prompt(self, session: Dict[str, Any], user_input: str) -> str:
        """
        Construit le prompt pour la conversation

        Args:
            session: Session de chat
            user_input: Message de l'utilisateur

        Returns:
            Prompt formaté pour le LLM
        """
        # Récupérer le contexte de conversation
        context = session.get("context", {})
        character_profile = context.get("character_profile", "")

        # Récupérer les messages récents (limité à 10 pour éviter les contextes trop longs)
        recent_messages = self.get_session_messages(session["id"], limit=10)

        # Construire le prompt
        prompt = f"""# PROFIL DE PERSONNAGE:
{character_profile}

# CONVERSATION:
"""

        # Ajouter les messages récents
        for msg in recent_messages:
            sender = "User" if msg["sender"] == "user" else "Assistant"
            prompt += f"{sender}: {msg['content']}\n"

        # Ajouter le nouveau message de l'utilisateur
        prompt += f"User: {user_input}\n"
        prompt += "Assistant: "

        return prompt

    def send_message(self, session_id: str, user_input: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Envoie un message dans une session et génère une réponse

        Args:
            session_id: ID de la session
            user_input: Message de l'utilisateur
            metadata: Métadonnées optionnelles

        Returns:
            Message généré par le personnage
        """
        try:
            # Récupérer la session
            session = self.get_session(session_id)
            character_id = session["character_id"]

            # Enregistrer le message de l'utilisateur
            timestamp = datetime.now().isoformat()
            user_message_id = str(uuid.uuid4())

            query = """
            INSERT INTO chat_messages (id, session_id, sender, content, character_id, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            db_manager.execute(
                query,
                (
                    user_message_id,
                    session_id,
                    "user",
                    user_input,
                    character_id,
                    timestamp,
                    json.dumps(metadata) if metadata else None
                )
            )

            # Mettre à jour le timestamp de la session
            query = "UPDATE chat_sessions SET updated_at = ? WHERE id = ?"
            db_manager.execute(query, (timestamp, session_id))

            # Trouver les mémoires pertinentes
            relevant_memories = self.memory_manager.get_relevant_memories(
                character_id, user_input)

            # Mettre à jour le contexte de la session avec les mémoires pertinentes
            if "context" not in session:
                session["context"] = {}
            session["context"]["relevant_memories"] = relevant_memories

            # Construire le prompt pour le LLM
            prompt = self._build_conversation_prompt(session, user_input)

            # Récupérer le système de prompt
            system_prompt = session.get("context", {}).get(
                "system_instructions", "Tu es un assistant IA conversationnel.")

            # Générer la réponse avec le LLM
            start_time = time.time()
            try:
                response_text = llm_service.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt
                )
            except Exception as e:
                logger.error(f"Erreur lors de la génération de réponse: {e}")
                response_text = self._generate_mock_response(prompt)

            generation_time = time.time() - start_time

            # Enregistrer la réponse générée
            assistant_message_id = str(uuid.uuid4())
            assistant_metadata = {
                "generation_time": generation_time,
                "model": "llama3"  # À remplacer par le modèle réel du service LLM
            }

            query = """
            INSERT INTO chat_messages (id, session_id, sender, content, character_id, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            db_manager.execute(
                query,
                (
                    assistant_message_id,
                    session_id,
                    "assistant",
                    response_text,
                    character_id,
                    datetime.now().isoformat(),
                    json.dumps(assistant_metadata)
                )
            )

            db_manager.commit()

            # Créer une mémoire à partir de la conversation
            memory_content = f"User: {user_input}\n{response_text}"
            memory_type = "conversation"
            self.memory_manager.create_memory(
                character_id=character_id,
                content=memory_content,
                memory_type=memory_type,
                importance=None  # Laisser le système calculer l'importance
            )

            # Retourner le message généré
            return {
                "id": assistant_message_id,
                "session_id": session_id,
                "character_id": character_id,
                "content": response_text,
                "sender": "assistant",
                "timestamp": datetime.now().isoformat(),
                "metadata": assistant_metadata
            }

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {e}")
            raise

    def _generate_mock_response(self, prompt: str) -> str:
        """
        Génère une réponse simulée en cas d'échec de génération LLM

        Args:
            prompt: Prompt de la conversation

        Returns:
            Réponse simulée
        """
        return llm_service._generate_mock_response(prompt)

    def add_message(self, session_id: str, content: str, role: str,
                    metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ajoute un message à une session de chat

        Args:
            session_id: ID de la session
            content: Contenu du message
            role: Rôle de l'émetteur (user/assistant)
            metadata: Métadonnées du message

        Returns:
            Message créé
        """
        try:
            session = self.get_session(session_id)

            # Créer le message
            timestamp = int(time.time())
            message_id = str(uuid.uuid4())

            message = {
                "id": message_id,
                "session_id": session_id,
                "content": content,
                "role": role,
                "timestamp": timestamp,
                "metadata": json.dumps(metadata) if metadata else None
            }

            # Insérer en base de données
            query = """
            INSERT INTO chat_messages (id, session_id, content, role, timestamp, metadata, memory_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            db_manager.execute(
                query,
                (
                    message_id,
                    session_id,
                    content,
                    role,
                    timestamp,
                    message["metadata"],
                    None  # memory_id
                )
            )

            # Mettre à jour le timestamp de la session
            query = "UPDATE chat_sessions SET updated_at = ? WHERE id = ?"
            db_manager.execute(query, (timestamp, session_id))

            # Trouver les mémoires pertinentes
            if role == "user":
                try:
                    memory_id = self.memory_manager.create_memory(
                        content,
                        session["character_id"],
                        type="conversation",
                        source=f"chat:{session_id}"
                    )

                    # Mettre à jour le message avec l'ID de la mémoire
                    if memory_id:
                        query = "UPDATE chat_messages SET memory_id = ? WHERE id = ?"
                        db_manager.execute(query, (memory_id, message_id))
                        message["memory_id"] = memory_id
                except Exception as e:
                    logger.error(
                        f"Erreur lors de la création de la mémoire: {e}")

            db_manager.commit()

            # Convertir les métadonnées JSON en dictionnaire
            if message.get("metadata"):
                message["metadata"] = json.loads(message["metadata"])

            return message

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du message: {e}")
            raise

    def generate_response(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Génère une réponse automatique à partir d'un message utilisateur

        Args:
            session_id: ID de la session
            user_message: Message de l'utilisateur

        Returns:
            Message généré par l'assistant
        """
        try:
            # Ajouter le message de l'utilisateur
            self.add_message(session_id, user_message, "user")

            # Récupérer la session
            session = self.get_session(session_id)

            # Récupérer les messages récents
            messages = self.get_session_messages(session_id)

            # Générer une réponse
            context = session.get("context", {})
            character_id = session.get("character_id")

            # Obtenir le contexte complet du personnage
            if character_id:
                character_context = self.character_manager.get_character_conversation_context(
                    character_id)
                if character_context:
                    if not context:
                        context = {}
                    context.update(character_context)

            # Créer un modèle de réponse vide
            timestamp = int(time.time())
            message_id = str(uuid.uuid4())

            # Si on est en mode simulation, générer une réponse fictive
            if context.get("simulation_mode"):
                response_content = self._generate_mock_response(
                    user_message, messages, context)
            else:
                # TODO: Intégrer avec le service LLM
                response_content = f"Je suis désolé, je ne peux pas répondre à ce message pour le moment."

            # Créer le message de réponse
            response = {
                "id": message_id,
                "session_id": session_id,
                "content": response_content,
                "role": "assistant",
                "timestamp": timestamp,
                "metadata": None
            }

            # Insérer en base de données
            query = """
            INSERT INTO chat_messages (id, session_id, content, role, timestamp, metadata, memory_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            db_manager.execute(
                query,
                (
                    message_id,
                    session_id,
                    response_content,
                    "assistant",
                    timestamp,
                    None,  # metadata
                    None  # memory_id
                )
            )

            # Mettre à jour le timestamp de la session
            query = "UPDATE chat_sessions SET updated_at = ? WHERE id = ?"
            db_manager.execute(query, (timestamp, session_id))

            db_manager.commit()

            return response

        except Exception as e:
            logger.error(f"Erreur lors de la génération de réponse: {e}")
            raise


# Instance globale du service de chat
chat_service = ChatService()
