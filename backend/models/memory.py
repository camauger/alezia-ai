"""
Module for character memory models
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator


class MemoryBase(BaseModel):
    """Base model for memories"""
    character_id: int = Field(...,
                              description="ID of the character associated with this memory")
    type: str = Field(...,
                      description="Type of memory (conversation, event, fact, thought)")
    content: str = Field(..., description="Content of the memory")
    importance: float = Field(
        1.0, description="Importance of the memory (1.0-10.0)")
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata")


class MemoryCreate(MemoryBase):
    """Model for creating a memory"""
    character_id: int
    content: str
    memory_type: str = "conversation"  # conversation, event, observation
    importance: float = 1.0
    source: str = "user"
    timestamp: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None

    @validator("importance")
    def check_importance(cls, v):
        if v < 0 or v > 10:
            raise ValueError("Importance must be between 0 and 10")
        return v

    @validator("memory_type")
    def check_memory_type(cls, v):
        allowed_types = ["conversation", "event", "observation", "reflection"]
        if v not in allowed_types:
            raise ValueError(
                f"Memory type must be one of the following: {', '.join(allowed_types)}")
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
    character_id: int = Field(...,
                              description="ID of the character associated with this fact")
    subject: str = Field(..., description="Subject of the fact (often a name)")
    predicate: str = Field(..., description="Predicate (relation, action)")
    object: str = Field(..., description="Object of the fact")
    confidence: float = Field(
        1.0, description="Confidence in this fact (0.0-1.0)")
    source_memory_id: Optional[int] = Field(
        None, description="ID of the source memory")


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
