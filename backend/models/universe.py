"""
Module pour les modèles d'univers et leurs éléments
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class UniverseBase(BaseModel):
    """Modèle de base pour les univers"""
    name: str = Field(..., description="Nom de l'univers")
    description: str = Field(..., description="Description générale de l'univers")
    type: str = Field(..., description="Type d'univers (fantasy, sci-fi, historical, etc.)")
    time_period: Optional[str] = Field(None, description="Période temporelle spécifique")
    rules: Optional[str] = Field(None, description="Règles particulières de cet univers")


class UniverseCreate(UniverseBase):
    """Modèle pour la création d'un univers"""
    pass


class Universe(UniverseBase):
    """Modèle complet d'un univers avec ses métadonnées"""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class UniverseElementBase(BaseModel):
    """Modèle de base pour les éléments d'un univers"""
    universe_id: int = Field(..., description="ID de l'univers auquel appartient cet élément")
    name: str = Field(..., description="Nom de l'élément")
    type: str = Field(..., description="Type d'élément (location, organization, item, concept, etc.)")
    description: str = Field(..., description="Description détaillée de l'élément")
    importance: int = Field(3, description="Importance de l'élément dans l'univers (1-5)")


class UniverseElementCreate(UniverseElementBase):
    """Modèle pour la création d'un élément d'univers"""
    pass


class UniverseElement(UniverseElementBase):
    """Modèle complet d'un élément d'univers avec ses métadonnées"""
    id: int

    class Config:
        orm_mode = True


class UniverseSummary(BaseModel):
    """Résumé d'un univers pour les listes"""
    id: int
    name: str
    type: str
    time_period: Optional[str] = None
    character_count: int = 0

    class Config:
        orm_mode = True


class UniverseDetail(Universe):
    """Détails complets d'un univers avec ses éléments"""
    elements: List[UniverseElement] = []
    characters: List[dict] = []

    class Config:
        orm_mode = True