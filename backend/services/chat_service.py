"""
Service de gestion des sessions de chat et intégration LLM (ORM SQLAlchemy).
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any

from backend.database import SessionLocal
from backend.models.chat import ChatSessionModel, MessageModel
from backend.models.memory import MemoryCreate
from backend.services.character_manager import CharacterManager
from backend.services.llm_service import llm_service
from backend.services.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ChatService:
    """Gère les sessions de chat et la génération de réponses via le LLM."""

    def __init__(self):
        self.character_manager = CharacterManager()
        self.memory_manager = MemoryManager()

    @staticmethod
    def _session_to_dict(s: ChatSessionModel) -> dict[str, Any]:
        return {
            "id": s.id,
            "user_id": s.user_id,
            "character_id": s.character_id,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            "active": s.active,
            "context": json.loads(s.context) if s.context else {},
        }

    @staticmethod
    def _message_to_dict(m: MessageModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "session_id": m.session_id,
            "sender": m.sender,
            "content": m.content,
            "character_id": m.character_id,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            "metadata": json.loads(m.message_metadata) if m.message_metadata else None,
        }

    def create_session(
        self, user_id: str, character_id: int, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        db = SessionLocal()
        try:
            character = self.character_manager.get_character(db, character_id)
            if not character:
                raise ValueError(f"Character {character_id} not found")

            session = ChatSessionModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                character_id=character_id,
                active=True,
                context=json.dumps(context or {}),
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return self._session_to_dict(session)
        finally:
            db.close()

    def get_session(self, session_id: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            session = db.query(ChatSessionModel).filter_by(id=session_id).first()
            if not session:
                raise ValueError(f"Session {session_id} not found")
            return self._session_to_dict(session)
        finally:
            db.close()

    def get_user_sessions(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            sessions = (
                db.query(ChatSessionModel)
                .filter_by(user_id=user_id)
                .order_by(ChatSessionModel.updated_at.desc())
                .limit(limit)
                .all()
            )
            return [self._session_to_dict(s) for s in sessions]
        finally:
            db.close()

    def get_session_messages(
        self, session_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            messages = (
                db.query(MessageModel)
                .filter_by(session_id=session_id)
                .order_by(MessageModel.timestamp.asc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [self._message_to_dict(m) for m in messages]
        finally:
            db.close()

    def delete_session(self, session_id: str) -> bool:
        db = SessionLocal()
        try:
            session = db.query(ChatSessionModel).filter_by(id=session_id).first()
            if not session:
                return False
            db.delete(session)  # cascade supprime les messages
            db.commit()
            return True
        finally:
            db.close()

    def _build_prompt(
        self, session_dict: dict[str, Any], user_input: str
    ) -> str:
        context = session_dict.get("context", {}) or {}
        character_profile = context.get("character_profile", "")

        recent = self.get_session_messages(session_dict["id"], limit=10)
        prompt = f"# CHARACTER PROFILE:\n{character_profile}\n\n# CONVERSATION:\n"
        for msg in recent:
            sender = "User" if msg["sender"] == "user" else "Assistant"
            prompt += f"{sender}: {msg['content']}\n"
        prompt += f"User: {user_input}\nAssistant: "
        return prompt

    def send_message(
        self,
        session_id: str,
        user_input: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        db = SessionLocal()
        try:
            session = db.query(ChatSessionModel).filter_by(id=session_id).first()
            if not session:
                raise ValueError(f"Session {session_id} not found")
            character_id = session.character_id

            # Message utilisateur
            db.add(
                MessageModel(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    sender="user",
                    content=user_input,
                    character_id=character_id,
                    message_metadata=json.dumps(metadata) if metadata else None,
                )
            )
            session.updated_at = datetime.now()
            db.commit()

            # Contexte mémoire (db passé correctement — corrige le bug latent)
            relevant = self.memory_manager.get_relevant_memories(
                db, character_id, user_input
            )
            session_dict = self._session_to_dict(session)
            session_dict.setdefault("context", {})["relevant_memories"] = [
                m.model_dump() for m in relevant
            ]

            prompt = self._build_prompt(session_dict, user_input)
            system_prompt = session_dict["context"].get(
                "system_instructions", "You are a conversational AI assistant."
            )

            start = time.time()
            response_text = llm_service.generate_text(
                prompt=prompt, system_prompt=system_prompt
            )
            generation_time = time.time() - start

            assistant_meta = {
                "generation_time": generation_time,
                "model": llm_service.default_model,
            }
            assistant_id = str(uuid.uuid4())
            db.add(
                MessageModel(
                    id=assistant_id,
                    session_id=session_id,
                    sender="assistant",
                    content=response_text,
                    character_id=character_id,
                    message_metadata=json.dumps(assistant_meta),
                )
            )
            session.updated_at = datetime.now()
            db.commit()

            # Mémoire de la conversation (db passé correctement)
            try:
                self.memory_manager.create_memory(
                    db,
                    MemoryCreate(
                        character_id=character_id,
                        content=f"User: {user_input}\n{response_text}",
                        memory_type="conversation",
                        importance=1.0,
                    ),
                )
            except Exception as e:
                logger.error(f"Erreur création mémoire: {e}")

            # Évolution des traits à partir de l'échange utilisateur
            try:
                self.character_manager.update_traits_from_interaction(
                    db, character_id, user_input, intensity=1.0
                )
            except Exception as e:
                logger.error(f"Erreur évolution des traits: {e}")

            return {
                "id": assistant_id,
                "session_id": session_id,
                "character_id": character_id,
                "content": response_text,
                "sender": "assistant",
                "timestamp": datetime.now().isoformat(),
                "metadata": assistant_meta,
            }
        finally:
            db.close()


# Instance globale du service de chat
chat_service = ChatService()
