"""
Module pour les modèles de relations entre personnages
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RelationshipBase(BaseModel):
    """Modèle de base pour les relations"""
    character_id: int = Field(..., description="ID du personnage source de la relation")
    target_name: str = Field(..., description="Nom du personnage ou de l'entité cible")
    sentiment: float = Field(0.0, description="Sentiment général (-1.0 négatif à 1.0 positif)")
    trust: float = Field(0.0, description="Niveau de confiance (0.0 à 1.0)")
    familiarity: float = Field(0.0, description="Niveau de familiarité (0.0 à 1.0)")
    notes: Optional[str] = Field(None, description="Notes additionnelles sur la relation")


class RelationshipCreate(RelationshipBase):
    """Modèle pour la création d'une relation"""
    pass


class Relationship(RelationshipBase):
    """Modèle complet d'une relation avec ses métadonnées"""
    id: int
    last_updated: datetime

    class Config:
        orm_mode = True


class RelationshipUpdate(BaseModel):
    """Modèle pour la mise à jour d'une relation"""
    sentiment: Optional[float] = None
    trust: Optional[float] = None
    familiarity: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        orm_mode = True


class UserCharacterRelationship(BaseModel):
    """Relation spécifique entre l'utilisateur et un personnage"""
    character_id: int
    username: str = "user"  # Par défaut, on utilise simplement "user"
    sentiment: float = 0.0
    trust: float = 0.0
    familiarity: float = 0.0
    interactions_count: int = 0
    last_interaction: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        orm_mode = True