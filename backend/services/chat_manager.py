"""
Service for managing chat sessions
"""

import asyncio
import datetime
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.models.chat import ChatSession as ChatSessionModel
from backend.models.chat import Message as MessageModel
from backend.models.memory import MemoryCreate

from .character_manager import character_manager
from .llm_service import llm_service
from .memory_manager import memory_manager
from .universe_manager import universe_manager

logger = logging.getLogger(__name__)


class ChatManager:
    """Chat session manager"""

    def create_session(self, db: Session, character_id: int) -> ChatSessionModel:
        """Creates a new chat session"""
        db_session = ChatSessionModel(character_id=character_id)
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        logger.info(
            f'Session created for character {character_id} (ID: {db_session.id})'
        )
        return db_session

    def get_session(self, db: Session, session_id: int) -> Optional[ChatSessionModel]:
        """Retrieves a chat session by its ID"""
        return (
            db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
        )

    def get_character_sessions(
        self, db: Session, character_id: int, limit: int = 10
    ) -> list[ChatSessionModel]:
        """Retrieves chat sessions for a character"""
        return (
            db.query(ChatSessionModel)
            .filter(ChatSessionModel.character_id == character_id)
            .order_by(ChatSessionModel.start_time.desc())
            .limit(limit)
            .all()
        )

    async def send_message(
        self, db: Session, session_id: int, content: str, is_user: bool = True
    ) -> dict[str, Any]:
        """Sends a message in a session and generates a response if necessary"""
        session = self.get_session(db, session_id)
        if not session:
            raise ValueError(f'Session not found (ID: {session_id})')

        character_id = session.character_id

        # Save the message
        db_message = MessageModel(
            session_id=session_id,
            is_user=is_user,
            content=content,
            timestamp=datetime.datetime.now(),
            metadata={},
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        logger.info(f'Message saved (ID: {db_message.id})')

        # If it's a user message, generate a response
        if is_user:
            # Store the message as a memory
            self._store_message_as_memory(db, character_id, content, is_user=True)

            # Generate a response
            response: dict[str, Any] = await self._generate_response(
                db, session_id, character_id, content
            )

            if 'error' not in response:
                # Store the response as a memory
                self._store_message_as_memory(
                    db, character_id, response['content'], is_user=False
                )

            return response

        return {
            'id': db_message.id,
            'content': content,
            'timestamp': db_message.timestamp.isoformat(),
        }

    async def _generate_response(
        self, db: Session, session_id: int, character_id: int, user_message: str
    ) -> dict[str, Any]:
        """Generates a response from the character"""
        character = character_manager.get_character(db, character_id)
        if not character:
            return {
                'content': 'Error: Character not found',
                'error': 'character_not_found',
            }

        universe_description = None
        if character.universe_id:
            universe = universe_manager.get_universe(db, character.universe_id)
            if universe:
                universe_description = universe_manager.get_universe_description(
                    db, universe.id
                )

        # Retrieve the character's state
        character_manager.get_character_state(db, character_id)

        relevant_memories = memory_manager.get_relevant_memories(
            db, character_id, user_message, limit=5
        )
        memory_context = ''
        if relevant_memories:
            memory_context = 'Here are some relevant memories for this conversation:\n'
            for i, memory in enumerate(relevant_memories):
                memory_context += f'{i + 1}. {memory.memory.content}\n'

        recent_messages = (
            db.query(MessageModel)
            .filter(MessageModel.session_id == session_id)
            .order_by(MessageModel.timestamp.desc())
            .limit(10)
            .all()
        )
        recent_messages.reverse()

        conversation_history = ''
        for msg in recent_messages:
            prefix = 'User: ' if msg.is_user else f'{character.name}: '
            conversation_history += f'{prefix}{msg.content}\n'

        system_prompt = llm_service.generate_text(
            prompt=f'System prompt for {character.name}',
            system_prompt=f'You are {character.name}, a character in the {universe_description} universe. Your personality is {character.personality} and your backstory is {character.backstory}.',
        )

        if memory_context:
            system_prompt += f'\n\n{memory_context}'

        prompt = conversation_history
        if not prompt:
            prompt = f'User: {user_message}\n{character.name}: '
        else:
            prompt += f'User: {user_message}\n{character.name}: '

        response_text = llm_service.generate_text(
            prompt=prompt, system_prompt=system_prompt
        )
        response = {'content': response_text}

        if 'error' not in response:
            db_message = MessageModel(
                session_id=session_id,
                is_user=False,
                content=response['content'],
                timestamp=datetime.datetime.now(),
                metadata={
                    'generation_time': response.get('generation_time'),
                    'tokens_used': response.get('tokens_used'),
                    'model': response.get('model'),
                },
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            response['id'] = db_message.id
            response['timestamp'] = db_message.timestamp.isoformat()

        return response

    def _store_message_as_memory(
        self, db: Session, character_id: int, content: str, is_user: bool
    ) -> int:
        """Stores a message as a memory for the character"""
        memory_type = 'user_message' if is_user else 'character_message'
        importance = 1.0

        memory = MemoryCreate(
            character_id=character_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
        )

        db_memory = memory_manager.create_memory(db, memory)
        return db_memory.id

    def end_session(self, db: Session, session_id: int) -> bool:
        """Ends a chat session"""
        db_session = self.get_session(db, session_id)
        if db_session:
            db_session.end_time = datetime.datetime.now()
            db.commit()
            asyncio.create_task(self._generate_session_summary(db, session_id))
            return True
        return False

    async def _generate_session_summary(self, db: Session, session_id: int) -> None:
        """Generates a session summary (in the background)"""
        try:
            session = self.get_session(db, session_id)
            if not session or not session.messages:
                return

            messages_content = ''
            for msg in session.messages:
                prefix = 'User' if msg.is_user else 'Character'
                messages_content += f'{prefix}: {msg.content}\n'

            prompt = f'Summarize the following conversation in a few sentences:\n\n{messages_content}\n\nSummary:'

            response = llm_service.generate_text(prompt=prompt, max_tokens=200)

            if response:
                session.summary = response
                db.commit()
                logger.info(f'Summary generated for session {session_id}')

        except Exception as e:
            logger.error(f'Error generating session summary: {e}')


# Global instance of the chat manager
chat_manager = ChatManager()
