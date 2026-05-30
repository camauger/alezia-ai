"""
Module for character memory models
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator, validator
from sqlalchemy import (
    JSON,
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

    @property
    def memory_type(self):
        """Alias for 'type' column, required by the Pydantic Memory model."""
        return self.type


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
    metadata: dict[str, Any] | None = Field(
        default_factory=dict, description="Additional metadata"
    )


class MemoryCreate(MemoryBase):
    """Model for creating a memory"""

    source: str = "user"
    timestamp: datetime | None = None

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
    last_accessed: datetime | None = None
    access_count: int = 0
    embedding_id: int | None = None

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def _remap_orm_fields(cls, values: Any) -> Any:
        """Map ORM attribute names to Pydantic field names when reading from ORM.

        MemoryModel uses:
          - .type          -> memory_type
          - .memory_metadata -> metadata  (avoids SQLAlchemy MetaData collision)
        """
        if hasattr(values, '__tablename__'):
            # values is an ORM model instance
            data: dict[str, Any] = {}
            for col in ('id', 'character_id', 'content', 'importance',
                        'created_at', 'last_accessed', 'access_count'):
                data[col] = getattr(values, col, None)
            data['memory_type'] = getattr(values, 'type', None)
            raw_meta = getattr(values, 'memory_metadata', None)
            data['metadata'] = raw_meta if isinstance(raw_meta, dict) else {}
            # source and timestamp/embedding_id have defaults; set safely
            data['source'] = getattr(values, 'source', 'user') or 'user'
            data['timestamp'] = getattr(values, 'created_at', None)
            data['embedding_id'] = None
            return data
        return values


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
    source_memory_id: int | None = Field(None, description="ID of the source memory")


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
