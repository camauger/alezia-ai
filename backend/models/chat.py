"""
Data models for conversations
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class ConversationContext(BaseModel):
    """Conversation context including character profile and relevant memories"""

    character_profile: str = Field(
        description="Full character profile formatted for the model"
    )
    recent_messages: Optional[list[dict[str, Any]]] = Field(
        default=[], description="Recent messages in the conversation"
    )
    relevant_memories: Optional[list[dict[str, Any]]] = Field(
        default=[], description="Relevant memories for the current context"
    )
    system_instructions: Optional[str] = Field(
        default=None, description="System instructions to guide the model"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Additional metadata for the context"
    )


class MessageMetadata(BaseModel):
    """Metadata for a message"""

    generation_time: Optional[float] = Field(
        default=None, description="Response generation time in seconds"
    )
    model: Optional[str] = Field(
        default=None, description="Model used to generate the response"
    )
    tokens_used: Optional[int] = Field(
        default=None, description="Number of tokens used to generate the response"
    )
    custom_data: Optional[dict[str, Any]] = Field(
        default=None, description="Additional custom data"
    )


class MessageCreate(BaseModel):
    """Model for creating a message"""

    session_id: str = Field(description="Chat session ID")
    content: str = Field(description="Message content")
    metadata: Optional[MessageMetadata] = Field(
        default=None, description="Message metadata"
    )


class ChatMessage(BaseModel):
    """Model for a chat message"""

    id: str = Field(description="Unique message ID")
    session_id: str = Field(description="Chat session ID")
    content: str = Field(description="Message content")
    sender: str = Field(description="Message sender (user or assistant)")
    character_id: Optional[int] = Field(
        default=None, description="Character ID (for assistant messages)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Message timestamp"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Message metadata"
    )


class SessionCreate(BaseModel):
    """Model for creating a session"""

    character_id: int = Field(description="Character ID")
    user_id: str = Field(description="User ID")
    context: Optional[ConversationContext] = Field(
        default=None, description="Initial conversation context"
    )


class ChatSession(BaseModel):
    """Model for a chat session"""

    id: str = Field(description="Unique session ID")
    user_id: str = Field(description="User ID")
    character_id: int = Field(description="Character ID")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Session creation date"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Session last update date"
    )
    active: bool = Field(default=True, description="Indicates if the session is active")
    context: Optional[ConversationContext] = Field(
        default=None, description="Conversation context"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Session metadata"
    )


# ============================================================================
# MODÈLES SQLAlchemy pour la base de données
# ============================================================================


class ChatSessionModel(Base):
    """Modèle SQLAlchemy pour les sessions de chat"""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.now, nullable=False)
    end_time = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)

    # Relations
    character = relationship("CharacterModel")
    messages = relationship(
        "MessageModel", back_populates="session", cascade="all, delete-orphan"
    )


class MessageModel(Base):
    """Modèle SQLAlchemy pour les messages de chat"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    is_user = Column(Boolean, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    message_metadata = Column(
        Text, nullable=True
    )  # JSON en tant que texte - renommé pour éviter conflit avec SQLAlchemy

    # Relations
    session = relationship("ChatSessionModel", back_populates="messages")


# ============================================================================
# Alias pour la compatibilité avec le code existant
# ============================================================================

# Alias pour les modèles Pydantic
Message = ChatMessage
