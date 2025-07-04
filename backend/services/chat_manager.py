"""
Service for managing chat sessions
"""

import asyncio
import datetime
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.models.memory import MemoryCreate
from backend.utils.db import db_manager  # type: ignore

from .character_manager import character_manager
from .llm_service import llm_service
from .memory_manager import memory_manager
from .universe_manager import universe_manager

logger = logging.getLogger(__name__)


class ChatManager:
    """Chat session manager"""

    def create_session(self, character_id: int) -> dict[str, Any]:
        """Creates a new chat session"""
        session_data = {
            "character_id": character_id,
            "start_time": datetime.datetime.now(),
            "end_time": None,
            "summary": None,
        }

        session_id = db_manager.insert("sessions", session_data)
        logger.info(f"Session created for character {character_id} (ID: {session_id})")

        return {
            "id": session_id,
            "character_id": character_id,
            "start_time": session_data["start_time"],
            "messages": [],
        }

    def get_session(self, session_id: int) -> Optional[dict[str, Any]]:
        """Retrieves a chat session by its ID"""
        session = db_manager.get_by_id("sessions", session_id)
        if not session:
            return None

        # Retrieve session messages
        query = "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC"
        messages = db_manager.execute_query(query, (session_id,))

        session["messages"] = messages
        return session

    def get_character_sessions(
        self, character_id: int, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Retrieves chat sessions for a character"""
        query = "SELECT * FROM sessions WHERE character_id = ? ORDER BY start_time DESC LIMIT ?"
        sessions = db_manager.execute_query(query, (character_id, limit))
        if sessions is None:
            return []
        if isinstance(sessions, dict):
            return [sessions]
        return sessions

    async def send_message(
        self, session_id: int, content: str, is_user: bool = True
    ) -> dict[str, Any]:
        """Sends a message in a session and generates a response if necessary"""
        session: dict[str, Any] | None = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found (ID: {session_id})")

        character_id = session["character_id"]

        # Save the message
        message_data = {
            "session_id": session_id,
            "is_user": is_user,
            "content": content,
            "timestamp": datetime.datetime.now(),
            "metadata": {},
        }

        message_id = db_manager.insert("messages", message_data)
        logger.info(f"Message saved (ID: {message_id})")

        # If it's a user message, generate a response
        if is_user:
            # Store the message as a memory
            self._store_message_as_memory(character_id, content, is_user=True)

            # Generate a response
            from backend.database import SessionLocal

            db = SessionLocal()
            try:
                response: dict[str, Any] = await self._generate_response(
                    db, session_id, character_id, content
                )
            finally:
                db.close()

            if "error" not in response:
                # Store the response as a memory
                self._store_message_as_memory(
                    character_id, response["content"], is_user=False
                )

            return response

        return {
            "id": message_id,
            "content": content,
            "timestamp": message_data["timestamp"].isoformat(),
        }

    async def _generate_response(
        self, db: Session, session_id: int, character_id: int, user_message: str
    ) -> dict[str, Any]:
        """Generates a response from the character"""
        # Retrieve the character
        character = character_manager.get_character(db, character_id)
        if not character:
            return {
                "content": "Error: Character not found",
                "error": "character_not_found",
            }

        # Retrieve the universe if available
        universe_description = None
        if character.universe_id:
            universe = universe_manager.get_universe(character.universe_id)
            if universe:
                universe_description = universe_manager.get_universe_description(
                    universe.id
                )

        # Retrieve the character's state
        character_state = character_manager.get_character_state(db, character_id)

        # Retrieve relevant memories
        relevant_memories = memory_manager.get_relevant_memories(
            character_id, user_message, limit=5
        )
        memory_context = ""
        if relevant_memories:
            memory_context = "Here are some relevant memories for this conversation:\n"
            for i, memory in enumerate(relevant_memories):
                memory_context += f"{i+1}. {memory.memory.content}\n"

        # Retrieve recent conversation history
        query = "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT 10"
        recent_messages = db_manager.execute_query(query, (session_id,))
        recent_messages.reverse()  # To have chronological order

        conversation_history = ""
        for msg in recent_messages:
            prefix = "User: " if msg["is_user"] else f"{character.name}: "
            conversation_history += f"{prefix}{msg['content']}\n"

        # Create the system prompt
        system_prompt = llm_service.generate_text(
            prompt=f"System prompt for {character.name}",
            system_prompt=f"You are {character.name}, a character in the {universe_description} universe. Your personality is {character.personality} and your backstory is {character.backstory}.",
        )

        if memory_context:
            system_prompt += f"\n\n{memory_context}"

        # Create the user prompt
        prompt = conversation_history
        if not prompt:
            prompt = f"User: {user_message}\n{character.name}: "
        else:
            prompt += f"User: {user_message}\n{character.name}: "

        # Generate the response
        response_text = llm_service.generate_text(
            prompt=prompt, system_prompt=system_prompt
        )
        response = {"content": response_text}

        # Save the response as a message
        if "error" not in response:
            message_data = {
                "session_id": session_id,
                "is_user": False,
                "content": response["content"],
                "timestamp": datetime.datetime.now(),
                "metadata": {
                    "generation_time": response.get("generation_time"),
                    "tokens_used": response.get("tokens_used"),
                    "model": response.get("model"),
                },
            }
            message_id = db_manager.insert("messages", message_data)
            response["id"] = message_id
            response["timestamp"] = message_data["timestamp"].isoformat()

        return response

    def _store_message_as_memory(
        self, character_id: int, content: str, is_user: bool
    ) -> int:
        """Stores a message as a memory for the character"""
        memory_type = "user_message" if is_user else "character_message"
        importance = 1.0  # Base importance

        memory = MemoryCreate(
            character_id=character_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
        )

        memory_id = memory_manager.create_memory(memory)
        return memory_id

    def end_session(self, session_id: int) -> bool:
        """Ends a chat session"""
        update_data = {"end_time": datetime.datetime.now()}
        rows_updated = db_manager.update(
            "sessions", update_data, "id = ?", (session_id,)
        )

        if rows_updated > 0:
            # Optional: Generate a session summary
            asyncio.create_task(self._generate_session_summary(session_id))

        return rows_updated > 0

    async def _generate_session_summary(self, session_id: int) -> None:
        """Generates a session summary (in the background)"""
        try:
            session = self.get_session(session_id)
            if not session or not session.get("messages"):
                return

            # Extract message content
            messages_content = ""
            for msg in session["messages"]:
                prefix = "User" if msg["is_user"] else "Character"
                messages_content += f"{prefix}: {msg['content']}\n"

            # Create a prompt to generate the summary
            prompt = f"Summarize the following conversation in a few sentences:\n\n{messages_content}\n\nSummary:"

            # Generate the summary
            response = llm_service.generate_text(prompt=prompt, max_tokens=200)

            # Update the session with the summary
            if response:
                update_data = {"summary": response}
                db_manager.update("sessions", update_data, "id = ?", (session_id,))
                logger.info(f"Summary generated for session {session_id}")

        except Exception as e:
            logger.error(f"Error generating session summary: {e}")


# Global instance of the chat manager
chat_manager = ChatManager()
