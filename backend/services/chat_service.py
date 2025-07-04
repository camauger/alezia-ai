"""
Service for managing chat sessions and LLM integration
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Optional

from backend.services.character_manager import CharacterManager
from backend.services.llm_service import llm_service
from backend.services.memory_manager import MemoryManager
from backend.utils.db import db_manager  # type: ignore

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat sessions and LLM integration"""

    def __init__(self):
        """Initializes the chat service"""
        self.sessions = {}  # Cache for active sessions
        self.character_manager = CharacterManager()
        self.memory_manager = MemoryManager()

    def create_session(
        self, user_id: str, character_id: int, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Creates a new chat session

        Args:
            user_id: User ID
            character_id: Character ID
            context: Optional conversation context

        Returns:
            Details of the created session
        """
        try:
            # Check if the character exists
            from backend.database import SessionLocal

            db = SessionLocal()
            try:
                character = self.character_manager.get_character(db, character_id)
            finally:
                db.close()

            if not character:
                logger.error(f'Character {character_id} not found')
                raise ValueError(f'Character {character_id} not found')

            # Generate a unique session ID
            session_id = str(uuid.uuid4())

            # Get the conversation context for this character
            if not context:
                context = {}

            # Create the session object
            timestamp = datetime.now().isoformat()
            session = {
                'id': session_id,
                'user_id': user_id,
                'character_id': character_id,
                'created_at': timestamp,
                'updated_at': timestamp,
                'context': context,
                'active': True,
                'messages': [],
            }

            # Store in the database
            session_data = {
                'id': session_id,
                'user_id': user_id,
                'character_id': character_id,
                'created_at': timestamp,
                'updated_at': timestamp,
                'context': json.dumps(context),
                'active': 1,
            }

            # Insert using the DB manager
            db_manager.insert('chat_sessions', session_data)

            # Cache it
            self.sessions[session_id] = session

            return session

        except Exception as e:
            logger.error(f'Error creating session: {e}')
            raise

    def get_session(self, session_id: str) -> dict[str, Any]:
        """
        Retrieves session details

        Args:
            session_id: Session ID

        Returns:
            Session details
        """
        # Check if in cache
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Otherwise, retrieve from the database
        session = db_manager.get_by_id('chat_sessions', session_id)

        if not session:
            raise ValueError(f'Session {session_id} not found')

        # Convert JSON context to a dictionary
        if session.get('context'):
            session['context'] = json.loads(session['context'])

        # Cache it
        self.sessions[session_id] = session

        return session

    def get_user_sessions(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Retrieves a user's session list

        Args:
            user_id: User ID
            limit: Maximum number of sessions to retrieve

        Returns:
            List of sessions
        """
        query = 'SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?'
        sessions = db_manager.execute_query(query, (user_id, limit))

        for session in sessions:
            if session.get('context'):
                session['context'] = json.loads(session['context'])

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Deletes a chat session

        Args:
            session_id: Session ID

        Returns:
            True if deletion was successful
        """
        try:
            # Delete associated messages
            db_manager.delete('chat_messages', 'session_id = ?', (session_id,))

            # Delete the session
            rows_deleted = db_manager.delete('chat_sessions', 'id = ?', (session_id,))

            # Remove from cache if present
            if session_id in self.sessions:
                del self.sessions[session_id]

            return rows_deleted > 0
        except Exception as e:
            logger.error(f'Error deleting session: {e}')
            return False

    def get_session_messages(
        self, session_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        Retrieves session messages

        Args:
            session_id: Session ID
            limit: Maximum number of messages to retrieve
            offset: Offset in the message list

        Returns:
            List of messages
        """
        query = """
        SELECT * FROM chat_messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
        LIMIT ? OFFSET ?
        """
        messages = db_manager.execute_query(query, (session_id, limit, offset))

        for message in messages:
            if message.get('metadata'):
                message['metadata'] = json.loads(message['metadata'])

        return messages

    def _build_conversation_prompt(
        self, session: dict[str, Any], user_input: str
    ) -> str:
        """
        Builds the conversation prompt

        Args:
            session: Chat session
            user_input: User's message

        Returns:
            Formatted prompt for the LLM
        """
        # Retrieve conversation context
        context = session.get('context', {})
        character_profile = context.get('character_profile', '')

        # Retrieve recent messages (limited to 10 to avoid overly long contexts)
        recent_messages = self.get_session_messages(session['id'], limit=10)

        # Build the prompt
        prompt = f"""# CHARACTER PROFILE:
{character_profile}

# CONVERSATION:
"""

        # Add recent messages
        for msg in recent_messages:
            sender = 'User' if msg['sender'] == 'user' else 'Assistant'
            prompt += f'{sender}: {msg["content"]}\n'

        # Add the new user message
        prompt += f'User: {user_input}\n'
        prompt += 'Assistant: '

        return prompt

    def send_message(
        self,
        session_id: str,
        user_input: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Sends a message in a session and generates a response

        Args:
            session_id: Session ID
            user_input: User's message
            metadata: Optional metadata

        Returns:
            Message generated by the character
        """
        try:
            # Retrieve the session
            session = self.get_session(session_id)
            character_id = session['character_id']

            # Save the user's message
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
                    'user',
                    user_input,
                    character_id,
                    timestamp,
                    json.dumps(metadata) if metadata else None,
                ),
            )

            # Update the session timestamp
            query = 'UPDATE chat_sessions SET updated_at = ? WHERE id = ?'
            db_manager.execute(query, (timestamp, session_id))

            # Find relevant memories
            relevant_memories = self.memory_manager.get_relevant_memories(
                character_id, user_input
            )

            # Update the session context with relevant memories
            if 'context' not in session:
                session['context'] = {}
            session['context']['relevant_memories'] = [
                mem.dict() for mem in relevant_memories
            ]

            # Build the prompt for the LLM
            prompt = self._build_conversation_prompt(session, user_input)

            # Retrieve the system prompt
            system_prompt = session.get('context', {}).get(
                'system_instructions', 'You are a conversational AI assistant.'
            )

            # Generate the response with the LLM
            start_time = time.time()
            try:
                response_text = llm_service.generate_text(
                    prompt=prompt, system_prompt=system_prompt
                )
            except Exception as e:
                logger.error(f'Error generating response: {e}')
                response_text = self._generate_mock_response(prompt, [], {})

            generation_time = time.time() - start_time

            # Save the generated response
            assistant_message_id = str(uuid.uuid4())
            assistant_metadata = {
                'generation_time': generation_time,
                'model': 'llama3',  # To be replaced with the actual model from the LLM service
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
                    'assistant',
                    response_text,
                    character_id,
                    datetime.now().isoformat(),
                    json.dumps(assistant_metadata),
                ),
            )

            db_manager.commit()

            # Create a memory from the conversation
            from backend.models.memory import MemoryCreate

            memory_content = f'User: {user_input}\n{response_text}'
            self.memory_manager.create_memory(
                MemoryCreate(
                    character_id=character_id,
                    content=memory_content,
                    memory_type='conversation',
                    importance=1.0,
                )
            )

            # Return the generated message
            return {
                'id': assistant_message_id,
                'session_id': session_id,
                'character_id': character_id,
                'content': response_text,
                'sender': 'assistant',
                'timestamp': datetime.now().isoformat(),
                'metadata': assistant_metadata,
            }

        except Exception as e:
            logger.error(f'Error sending message: {e}')
            raise

    def _generate_mock_response(
        self, user_message: str, messages: list[dict[str, Any]], context: dict[str, Any]
    ) -> str:
        """
        Generates a mock response in case of LLM generation failure

        Args:
            user_message: User's message
            messages: List of previous messages
            context: Conversation context

        Returns:
            Mock response
        """
        return llm_service._generate_mock_response(user_message)

    def add_message(
        self,
        session_id: str,
        content: str,
        role: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Adds a message to a chat session

        Args:
            session_id: Session ID
            content: Message content
            role: Sender's role (user/assistant)
            metadata: Message metadata

        Returns:
            Created message
        """
        try:
            session = self.get_session(session_id)

            # Create the message
            timestamp = int(time.time())
            message_id = str(uuid.uuid4())

            message = {
                'id': message_id,
                'session_id': session_id,
                'content': content,
                'role': role,
                'timestamp': timestamp,
                'metadata': json.dumps(metadata) if metadata else None,
            }

            # Insert into the database
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
                    message['metadata'],
                    None,  # memory_id
                ),
            )

            # Update the session timestamp
            query = 'UPDATE chat_sessions SET updated_at = ? WHERE id = ?'
            db_manager.execute(query, (timestamp, session_id))

            character_id = session.get('character_id')
            if not character_id:
                logger.warning(f'Session {session_id} has no character_id')
                db_manager.commit()
                return message

            # Update personality traits based on message content
            if role == 'user':
                # User messages have a stronger impact on the character's traits
                try:
                    # First, create a memory
                    from backend.models.memory import MemoryCreate

                    memory_id = self.memory_manager.create_memory(
                        MemoryCreate(
                            character_id=character_id,
                            content=content,
                            memory_type='conversation',
                            importance=1.0,
                            source=f'chat:{session_id}',
                        )
                    )

                    # Update the message with the memory ID
                    if memory_id:
                        query = 'UPDATE chat_messages SET memory_id = ? WHERE id = ?'
                        db_manager.execute(query, (memory_id, message_id))
                        message['memory_id'] = memory_id

                    # Update personality traits based on the content
                    from backend.database import SessionLocal

                    db = SessionLocal()
                    try:
                        self.character_manager.update_traits_from_interaction(
                            db,
                            character_id,
                            content,
                            intensity=1.0,  # Strong impact from user messages
                        )
                    finally:
                        db.close()
                except Exception as e:
                    logger.error(f'Error processing user message: {e}')

            elif role == 'assistant':
                # The character's responses also reflect their traits
                try:
                    # Update personality traits based on the response
                    # (weaker impact as it's an expression of existing traits)
                    from backend.database import SessionLocal

                    db = SessionLocal()
                    try:
                        self.character_manager.update_traits_from_interaction(
                            db,
                            character_id,
                            content,
                            intensity=0.3,  # Weaker impact from the character's responses
                        )
                    finally:
                        db.close()
                except Exception as e:
                    logger.error(f'Error processing character response: {e}')

            db_manager.commit()

            # Convert JSON metadata to a dictionary
            if message.get('metadata'):
                message['metadata'] = json.loads(message['metadata'])

            return message

        except Exception as e:
            logger.error(f'Error adding message: {e}')
            raise

    def generate_response(self, session_id: str, user_message: str) -> dict[str, Any]:
        """
        Generates an automatic response from a user message

        Args:
            session_id: Session ID
            user_message: User's message

        Returns:
            Message generated by the assistant
        """
        try:
            # Add the user's message
            self.add_message(session_id, user_message, 'user')

            # Retrieve the session
            session = self.get_session(session_id)

            # Retrieve recent messages
            messages = self.get_session_messages(session_id)

            # Generate a response
            context = session.get('context', {})
            character_id = session.get('character_id')

            # Get the full character context
            if character_id:
                context = {}

            # Create an empty response model
            timestamp = int(time.time())
            message_id = str(uuid.uuid4())

            # If in simulation mode, generate a mock response
            if context.get('simulation_mode'):
                response_content = self._generate_mock_response(
                    user_message, messages, context
                )
            else:
                # TODO: Integrate with the LLM service
                response_content = (
                    "I'm sorry, I can't respond to this message at the moment."
                )

            # Create the response message
            response = {
                'id': message_id,
                'session_id': session_id,
                'content': response_content,
                'role': 'assistant',
                'timestamp': timestamp,
                'metadata': None,
            }

            # Insert into the database
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
                    'assistant',
                    timestamp,
                    None,  # metadata
                    None,  # memory_id
                ),
            )

            # Update the session timestamp
            query = 'UPDATE chat_sessions SET updated_at = ? WHERE id = ?'
            db_manager.execute(query, (timestamp, session_id))

            db_manager.commit()

            return response

        except Exception as e:
            logger.error(f'Error generating response: {e}')
            raise


# Global instance of the chat service
chat_service = ChatService()
