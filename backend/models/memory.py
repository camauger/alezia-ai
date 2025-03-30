"""
Module pour les modèles de mémoire des personnages
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator


class MemoryBase(BaseModel):
    """Modèle de base pour les mémoires"""
    character_id: int = Field(...,
                              description="ID du personnage associé à cette mémoire")
    type: str = Field(...,
                      description="Type de mémoire (conversation, event, fact, thought)")
    content: str = Field(..., description="Contenu de la mémoire")
    importance: float = Field(
        1.0, description="Importance de la mémoire (1.0-10.0)")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Métadonnées additionnelles")


class MemoryCreate(MemoryBase):
    """Modèle pour la création d'une mémoire"""
    character_id: int
    content: str
    memory_type: str = "conversation"  # conversation, event, observation
    importance: float = 1.0
    source: str = "user"
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("importance")
    def check_importance(cls, v):
        if v < 0 or v > 10:
            raise ValueError("L'importance doit être entre 0 et 10")
        return v

    @validator("memory_type")
    def check_memory_type(cls, v):
        allowed_types = ["conversation", "event", "observation", "reflection"]
        if v not in allowed_types:
            raise ValueError(
                f"Le type de mémoire doit être l'un des suivants: {', '.join(allowed_types)}")
        return v

    @validator("timestamp", pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.now()


class Memory(MemoryCreate):
    """Modèle complet d'une mémoire avec ses métadonnées"""
    id: int
    created_at: datetime
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    embedding_id: Optional[int] = None

    class Config:
        orm_mode = True


class RetrievedMemory(BaseModel):
    """Mémoire récupérée avec sa pertinence"""
    memory: Memory
    relevance_score: float
    similarity_score: float
    recency_score: float
    importance_score: float

    class Config:
        orm_mode = True


class FactBase(BaseModel):
    """Modèle de base pour les faits extraits des mémoires"""
    character_id: int = Field(...,
                              description="ID du personnage associé à ce fait")
    subject: str = Field(..., description="Sujet du fait (souvent un nom)")
    predicate: str = Field(..., description="Prédicat (relation, action)")
    object: str = Field(..., description="Objet du fait")
    confidence: float = Field(
        1.0, description="Confiance dans ce fait (0.0-1.0)")
    source_memory_id: Optional[int] = Field(
        None, description="ID de la mémoire source")


class FactCreate(FactBase):
    """Modèle pour la création d'un fait"""
    pass


class Fact(FactBase):
    """Modèle complet d'un fait avec ses métadonnées"""
    id: int
    created_at: datetime
    last_confirmed: datetime

    class Config:
        orm_mode = True
