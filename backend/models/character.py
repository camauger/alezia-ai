"""
Module pour les modèles de personnages et leurs caractéristiques
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator


class CharacterTrait(BaseModel):
    """Modèle pour un trait de personnalité qui peut évoluer"""
    name: str = Field(...,
                      description="Nom du trait de personnalité",
                      min_length=2,
                      max_length=50)
    value: float = Field(...,
                         description="Valeur numérique du trait (-1.0 à 1.0)",
                         ge=-1.0,
                         le=1.0)
    category: str = Field(...,
                          description="Catégorie du trait (émotionnel, social, etc.)",
                          min_length=2,
                          max_length=30)
    description: str = Field(...,
                             description="Description de ce que signifie ce trait",
                             min_length=10)
    volatility: float = Field(0.2,
                              description="Facilité avec laquelle ce trait peut changer (0.0 à 1.0)",
                              ge=0.0,
                              le=1.0)

    @validator('value')
    def validate_value(cls, v):
        # Garantit que la valeur reste entre -1.0 et 1.0
        return max(-1.0, min(1.0, v))

    @validator('volatility')
    def validate_volatility(cls, v):
        # Garantit que la volatilité reste entre 0.0 et 1.0
        return max(0.0, min(1.0, v))


class PersonalityTraits(BaseModel):
    """Collection de traits de personnalité"""
    traits: List[CharacterTrait] = Field(default_factory=list,
                                         description="Liste des traits de personnalité")
    last_updated: datetime = Field(default_factory=datetime.now,
                                   description="Date de dernière mise à jour des traits")

    def to_dict(self) -> Dict[str, float]:
        """Convertit les traits en dictionnaire {nom: valeur}"""
        return {trait.name: trait.value for trait in self.traits}

    def get_trait_value(self, trait_name: str) -> float:
        """Récupère la valeur d'un trait spécifique"""
        for trait in self.traits:
            if trait.name.lower() == trait_name.lower():
                return trait.value
        return 0.0  # Valeur par défaut si le trait n'existe pas


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
    initial_traits: Optional[List[Dict[str, Any]]] = Field(None,
                                                           description="Traits de personnalité initiaux")


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
    active_traits: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Traits de personnalité actifs avec leurs valeurs actuelles"
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


class TraitChange(BaseModel):
    """Représente un changement dans un trait de personnalité"""
    trait_name: str
    old_value: float
    new_value: float
    change_amount: float
    reason: str
    timestamp: datetime = Field(default_factory=datetime.now)

    @root_validator(skip_on_failure=True)
    def compute_change(cls, values):
        old = values.get('old_value', 0)
        new = values.get('new_value', 0)
        values['change_amount'] = new - old
        return values
