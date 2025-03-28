"""
Module pour les modèles de mémoire des personnages
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class MemoryBase(BaseModel):
    """Modèle de base pour les mémoires"""
    character_id: int = Field(..., description="ID du personnage associé à cette mémoire")
    type: str = Field(..., description="Type de mémoire (conversation, event, fact, thought)")
    content: str = Field(..., description="Contenu de la mémoire")
    importance: float = Field(1.0, description="Importance de la mémoire (1.0-10.0)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Métadonnées additionnelles")


class MemoryCreate(MemoryBase):
    """Modèle pour la création d'une mémoire"""
    pass


class Memory(MemoryBase):
    """Modèle complet d'une mémoire avec ses métadonnées"""
    id: int
    created_at: datetime
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    embedding: Optional[List[float]] = None

    class Config:
        orm_mode = True


class RetrievedMemory(BaseModel):
    """Mémoire récupérée avec sa pertinence"""
    id: int
    content: str
    type: str
    importance: float
    created_at: datetime
    relevance: float = Field(1.0, description="Pertinence de cette mémoire pour le contexte actuel")
    recency: float = Field(1.0, description="Récence de cette mémoire (valeur normalisée)")

    class Config:
        orm_mode = True


class FactBase(BaseModel):
    """Modèle de base pour les faits extraits des mémoires"""
    character_id: int = Field(..., description="ID du personnage associé à ce fait")
    subject: str = Field(..., description="Sujet du fait (souvent un nom)")
    predicate: str = Field(..., description="Prédicat (relation, action)")
    object: str = Field(..., description="Objet du fait")
    confidence: float = Field(1.0, description="Confiance dans ce fait (0.0-1.0)")
    source_memory_id: Optional[int] = Field(None, description="ID de la mémoire source")


class FactCreate(FactBase):
    """Modèle pour la création d'un fait"""
    pass


class Fact(FactBase):
    """Modèle complet d'un fait avec ses métadonnées"""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True