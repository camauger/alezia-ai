"""
Module pour les modèles de personnages et leurs caractéristiques
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class CharacterBase(BaseModel):
    """Modèle de base pour les personnages"""
    name: str = Field(...,
                      description="Nom du personnage",
                      min_length=2,
                      max_length=100)
    description: str = Field(...,
                             description="Description physique et comportementale",
                             min_length=10)
    personality: str = Field(...,
                             description="Traits de personnalité et comportement",
                             min_length=10)
    backstory: Optional[str] = Field(None,
                                     description="Histoire personnelle du personnage")
    universe_id: Optional[int] = Field(None,
                                       description="ID de l'univers auquel appartient le personnage",
                                       ge=1)

    @validator('name')
    def name_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError(
                'Le nom ne peut pas être vide ou contenir uniquement des espaces')
        return v.strip()

    @validator('description', 'personality')
    def text_fields_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError(
                'Ce champ ne peut pas être vide ou contenir uniquement des espaces')
        return v.strip()


class CharacterCreate(CharacterBase):
    """Modèle pour la création d'un personnage"""
    pass


class Character(CharacterBase):
    """Modèle complet d'un personnage avec ses métadonnées"""
    id: int
    created_at: datetime
    universe: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True  # Pour rétrocompatibilité avec les anciens codes


class CharacterSummary(BaseModel):
    """Résumé d'un personnage pour les listes"""
    id: int
    name: str
    description: str
    universe: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True  # Pour rétrocompatibilité avec les anciens codes


class CharacterState(BaseModel):
    """État actuel d'un personnage dans une session"""
    character_id: int
    mood: str = Field("neutral",
                      description="Humeur actuelle du personnage",
                      pattern="^(cheerful|friendly|neutral|annoyed|angry)$")
    current_context: Dict[str, Any] = Field(default_factory=dict,
                                            description="Contexte actuel de la conversation")
    recent_memories: List[Dict[str, Any]] = Field(default_factory=list,
                                                  description="Souvenirs récents")
    relationship_to_user: Dict[str, Any] = Field(
        default_factory=lambda: {"sentiment": 0.0,
                                 "trust": 0.0, "familiarity": 0.0},
        description="État de la relation avec l'utilisateur"
    )

    @validator('mood')
    def mood_must_be_valid(cls, v):
        valid_moods = ["cheerful", "friendly", "neutral", "annoyed", "angry"]
        if v not in valid_moods:
            raise ValueError(
                f'Humeur invalide. Valeurs acceptées: {", ".join(valid_moods)}')
        return v

    class Config:
        from_attributes = True
        orm_mode = True  # Pour rétrocompatibilité avec les anciens codes
