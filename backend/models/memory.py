"""
Module for character memory models
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class MemoryModel(Base):
    """SQLAlchemy model for memories"""

    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(String, nullable=False)  # Maps to memory_type in Pydantic
    content = Column(Text, nullable=False)
    importance = Column(Float, default=1.0)
    memory_metadata = Column(
        "metadata", JSON
    )  # Use different attribute name to avoid conflict
    embedding = Column(JSON)  # Store as JSON array
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    last_accessed = Column(DateTime)
    access_count = Column(Integer, default=0)

    # Relationship
    character = relationship("CharacterModel", back_populates="memories")
    facts = relationship("FactModel", back_populates="source_memory")


class FactModel(Base):
    """SQLAlchemy model for facts"""

    __tablename__ = "facts"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject = Column(String, nullable=False)
    predicate = Column(String, nullable=False)
    object = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)
    source_memory_id = Column(Integer, ForeignKey("memories.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    last_confirmed = Column(DateTime, default=datetime.now, nullable=False)

    # Relationships
    character = relationship("CharacterModel", back_populates="facts")
    source_memory = relationship("MemoryModel", back_populates="facts")


class MemoryType(str, Enum):
    CONVERSATION = "conversation"
    EVENT = "event"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    USER_MESSAGE = "user_message"
    CHARACTER_MESSAGE = "character_message"
    FACTS_EXTRACTION = "facts_extraction"


class MemoryBase(BaseModel):
    """Base model for memories"""

    character_id: int = Field(
        ..., description="ID of the character associated with this memory"
    )
    memory_type: MemoryType = Field(
        ..., description="Type of memory (conversation, event, fact, thought)"
    )
    content: str = Field(..., description="Content of the memory")
    importance: float = Field(1.0, description="Importance of the memory (1.0-10.0)")
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class MemoryCreate(MemoryBase):
    """Model for creating a memory"""

    source: str = "user"
    timestamp: Optional[datetime] = None

    @validator("importance")
    def check_importance(cls, v):
        if v < 0 or v > 10:
            raise ValueError("Importance must be between 0 and 10")
        return v

    @validator("timestamp", pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.now()


class Memory(MemoryCreate):
    """Complete model of a memory with its metadata"""

    id: int
    created_at: datetime
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    embedding_id: Optional[int] = None

    class Config:
        from_attributes = True


class RetrievedMemory(BaseModel):
    """Retrieved memory with its relevance"""

    memory: Memory
    relevance_score: float
    similarity_score: float
    recency_score: float
    importance_score: float

    class Config:
        from_attributes = True


class FactBase(BaseModel):
    """Base model for facts extracted from memories"""

    character_id: int = Field(
        ..., description="ID of the character associated with this fact"
    )
    subject: str = Field(..., description="Subject of the fact (often a name)")
    predicate: str = Field(..., description="Predicate (relation, action)")
    object: str = Field(..., description="Object of the fact")
    confidence: float = Field(1.0, description="Confidence in this fact (0.0-1.0)")
    source_memory_id: Optional[int] = Field(None, description="ID of the source memory")


class FactCreate(FactBase):
    """Model for creating a fact"""

    pass


class Fact(FactBase):
    """Complete model of a fact with its metadata"""

    id: int
    created_at: datetime
    last_confirmed: datetime

    class Config:
        from_attributes = True
