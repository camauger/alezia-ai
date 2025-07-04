"""
Service for managing chat sessions
"""

import asyncio
import datetime
import json
import logging
from typing import Any, Optional

from backend.models.memory import MemoryCreate
from backend.utils.db import db_manager

from .llm_service import llm_service
from .memory_manager import memory_manager

logger = logging.getLogger(__name__)


class ChatManager:
    """Chat session manager using db_manager"""

    def create_session(self, character_id: int, user_id: str = "default_user") -> int:
        """Creates a new chat session"""
        session_data = {
            "character_id": character_id,
            "user_id": user_id,
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": None,
            "summary": None,
        }

        session_id = db_manager.insert("chat_sessions", session_data)
        db_manager.commit()

        logger.info(f"Session created for character {character_id} (ID: {session_id})")
        return session_id

    def get_session(self, session_id: int) -> Optional[dict[str, Any]]:
        """Retrieves a chat session by its ID"""
        return db_manager.get_by_id("chat_sessions", session_id)

    def get_character_sessions(
        self, character_id: int, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Retrieves chat sessions for a character"""
        query = """
            SELECT * FROM chat_sessions
            WHERE character_id = ?
            ORDER BY start_time DESC
            LIMIT ?
        """
        return db_manager.execute_query(query, (character_id, limit))

    async def send_message(
        self, session_id: int, content: str, is_user: bool = True
    ) -> dict[str, Any]:
        """Sends a message in a session and generates a response if necessary"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found (ID: {session_id})")

        character_id = session["character_id"]

        # Save the message
        message_data = {
            "session_id": session_id,
            "is_user": is_user,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat(),
            "message_metadata": json.dumps({}),
        }

        message_id = db_manager.insert("chat_messages", message_data)
        db_manager.commit()

        logger.info(f"Message saved (ID: {message_id})")

        # If it's a user message, generate a response
        if is_user:
            # Store the message as a memory
            self._store_message_as_memory(character_id, content, is_user=True)

            # Generate a response
            response = await self._generate_response(session_id, character_id, content)

            if "error" not in response:
                # Store the response as a memory
                self._store_message_as_memory(
                    character_id, response["content"], is_user=False
                )

            return response

        return {
            "id": message_id,
            "content": content,
            "timestamp": message_data["timestamp"],
        }

    async def _generate_response(
        self, session_id: int, character_id: int, user_message: str
    ) -> dict[str, Any]:
        """Generates a response from the character"""
        # Get character information
        character = db_manager.get_by_id("characters", character_id)
        if not character:
            return {
                "content": "Error: Character not found",
                "error": "character_not_found",
            }

        # Get universe description if available
        universe_description = "modern world"
        if character.get("universe_id"):
            universe = db_manager.get_by_id("universes", character["universe_id"])
            if universe:
                universe_description = f"{universe['name']}: {universe['description']}"

        # Get relevant memories (simplified)
        memory_context = ""
        try:
            # Get recent memories for context
            query = """
                SELECT content FROM memories
                WHERE character_id = ?
                ORDER BY created_at DESC
                LIMIT 5
            """
            memories = db_manager.execute_query(query, (character_id,))
            if memories:
                memory_context = "Recent memories:\n"
                for i, memory in enumerate(memories):
                    memory_context += f"{i + 1}. {memory['content']}\n"
        except Exception as e:
            logger.warning(f"Could not retrieve memories: {e}")

        # Get recent messages for conversation history
        query = """
            SELECT is_user, content FROM chat_messages
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """
        recent_messages = db_manager.execute_query(query, (session_id,))
        recent_messages.reverse()  # Chronological order

        conversation_history = ""
        for msg in recent_messages:
            prefix = "User: " if msg["is_user"] else f"{character['name']}: "
            conversation_history += f"{prefix}{msg['content']}\n"

        # Build system prompt
        system_prompt = f"""You are {character['name']}.
Personality: {character['personality']}
Description: {character['description']}
Universe: {universe_description}

{memory_context}"""

        # Build conversation prompt
        prompt = conversation_history
        if not prompt:
            prompt = f"User: {user_message}\n{character['name']}: "
        else:
            prompt += f"User: {user_message}\n{character['name']}: "

        # Generate response using LLM service
        response_text = llm_service.generate_text(
            prompt=prompt, system_prompt=system_prompt
        )

        response = {"content": response_text}

        # Save the response message
        response_data = {
            "session_id": session_id,
            "is_user": False,
            "content": response_text,
            "timestamp": datetime.datetime.now().isoformat(),
            "message_metadata": json.dumps(
                {
                    "generation_time": None,
                    "tokens_used": None,
                    "model": "ollama",
                }
            ),
        }

        message_id = db_manager.insert("chat_messages", response_data)
        db_manager.commit()

        response["id"] = message_id
        response["timestamp"] = response_data["timestamp"]

        return response

    def _store_message_as_memory(
        self, character_id: int, content: str, is_user: bool
    ) -> int:
        """Stores a message as a memory for the character"""
        memory_type = "conversation"
        importance = 1.0

        memory_data = {
            "character_id": character_id,
            "type": memory_type,
            "content": content,
            "importance": importance,
            "metadata": json.dumps({"is_user": is_user}),
            "created_at": datetime.datetime.now().isoformat(),
            "last_accessed": datetime.datetime.now().isoformat(),
            "access_count": 0,
        }

        memory_id = db_manager.insert("memories", memory_data)
        db_manager.commit()

        return memory_id

    def end_session(self, session_id: int) -> bool:
        """Ends a chat session"""
        session = self.get_session(session_id)
        if session:
            end_time = datetime.datetime.now().isoformat()
            db_manager.update("chat_sessions", session_id, {"end_time": end_time})
            db_manager.commit()

            # Generate summary in background (simplified)
            asyncio.create_task(self._generate_session_summary(session_id))
            return True
        return False

    async def _generate_session_summary(self, session_id: int) -> None:
        """Generates a session summary (in the background)"""
        try:
            session = self.get_session(session_id)
            if not session:
                return

            # Get all messages from this session
            query = """
                SELECT is_user, content FROM chat_messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """
            messages = db_manager.execute_query(query, (session_id,))

            if not messages:
                return

            messages_content = ""
            for msg in messages:
                prefix = "User" if msg["is_user"] else "Character"
                messages_content += f"{prefix}: {msg['content']}\n"

            prompt = f"Summarize the following conversation in a few sentences:\n\n{messages_content}\n\nSummary:"

            response = llm_service.generate_text(prompt=prompt, max_tokens=200)

            if response:
                db_manager.update("chat_sessions", session_id, {"summary": response})
                db_manager.commit()
                logger.info(f"Summary generated for session {session_id}")

        except Exception as e:
            logger.error(f"Error generating session summary: {e}")

    def get_session_history(
        self, session_id: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get message history for a session"""
        query = """
            SELECT id, is_user, content, timestamp, message_metadata
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """
        return db_manager.execute_query(query, (session_id, limit))

    def delete_session(self, session_id: int) -> bool:
        """Delete a chat session and all its messages"""
        try:
            # Delete messages first
            db_manager.execute(
                "DELETE FROM chat_messages WHERE session_id = ?", (session_id,)
            )

            # Delete session
            rows_deleted = db_manager.delete("chat_sessions", "id = ?", (session_id,))
            db_manager.commit()

            return rows_deleted > 0
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False


# Global instance of the chat manager
chat_manager = ChatManager()
