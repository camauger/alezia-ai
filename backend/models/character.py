"""
Module for character models and their characteristics
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, root_validator, validator
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class CharacterModel(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    personality = Column(Text)
    backstory = Column(Text, nullable=True)
    universe_id = Column(Integer, ForeignKey("universes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    universe = relationship("UniverseModel", back_populates="characters")
    traits = relationship("TraitModel", back_populates="character")
    relationships = relationship("RelationshipModel", back_populates="character")

class TraitModel(Base):
    __tablename__ = "personality_traits"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    name = Column(String)
    value = Column(Float)
    category = Column(String)
    description = Column(Text)
    volatility = Column(Float, default=0.2)
    last_updated = Column(DateTime, default=datetime.now)

    character = relationship("CharacterModel", back_populates="traits")
    changes = relationship("TraitChangeModel", back_populates="trait")

class TraitChangeModel(Base):
    __tablename__ = "trait_changes"

    id = Column(Integer, primary_key=True, index=True)
    trait_id = Column(Integer, ForeignKey("personality_traits.id"))
    character_id = Column(Integer, ForeignKey("characters.id"))
    old_value = Column(Float)
    new_value = Column(Float)
    change_amount = Column(Float)
    reason = Column(String)
    timestamp = Column(DateTime, default=datetime.now)

    trait = relationship("TraitModel", back_populates="changes")

# Pydantic models (for API validation and serialization)

class CharacterTrait(BaseModel):
    """Model for a personality trait that can evolve"""
    name: str = Field(...,
                      description="Name of the personality trait",
                      min_length=2,
                      max_length=50)
    value: float = Field(...,
                         description="Numeric value of the trait (-1.0 to 1.0)",
                         ge=-1.0,
                         le=1.0)
    category: str = Field(...,
                          description="Category of the trait (emotional, social, etc.)",
                          min_length=2,
                          max_length=30)
    description: str = Field(...,
                             description="Description of what this trait means",
                             min_length=10)
    volatility: float = Field(0.2,
                              description="Ease with which this trait can change (0.0 to 1.0)",
                              ge=0.0,
                              le=1.0)

    @validator('value')
    def validate_value(cls, v):
        # Ensures the value remains between -1.0 and 1.0
        return max(-1.0, min(1.0, v))

    @validator('volatility')
    def validate_volatility(cls, v):
        # Ensures volatility remains between 0.0 and 1.0
        return max(0.0, min(1.0, v))

    class Config:
        from_attributes = True


class PersonalityTraits(BaseModel):
    """Collection of personality traits"""
    traits: list[CharacterTrait] = Field(default_factory=list,
                                         description="List of personality traits")
    last_updated: datetime = Field(default_factory=datetime.now,
                                   description="Date of last trait update")

    def to_dict(self) -> dict[str, float]:
        """Converts traits to a dictionary {name: value}"""
        return {trait.name: trait.value for trait in self.traits}

    def get_trait_value(self, trait_name: str) -> float:
        """Retrieves the value of a specific trait"""
        for trait in self.traits:
            if trait.name.lower() == trait_name.lower():
                return trait.value
        return 0.0  # Default value if the trait does not exist


class CharacterBase(BaseModel):
    """Base model for characters"""
    name: str = Field(...,
                      description="Name of the character",
                      min_length=2,
                      max_length=100)
    description: str = Field(...,
                             description="Physical and behavioral description",
                             min_length=10)
    personality: str = Field(...,
                             description="Personality traits and behavior",
                             min_length=10)
    backstory: Optional[str] = Field(None,
                                     description="Personal history of the character")
    universe_id: Optional[int] = Field(None,
                                       description="ID of the universe the character belongs to",
                                       ge=1)

    @validator('name')
    def name_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError(
                'Name cannot be empty or contain only spaces')
        return v.strip()

    @validator('description', 'personality')
    def text_fields_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError(
                'This field cannot be empty or contain only spaces')
        return v.strip()


class CharacterCreate(CharacterBase):
    """Model for creating a character"""
    initial_traits: Optional[list[dict[str, Any]]] = Field(None,
                                                           description="Initial personality traits")


class Character(CharacterBase):
    """Complete model of a character with its metadata"""
    id: int
    created_at: datetime
    universe: Optional[str] = None

    class Config:
        from_attributes = True


class CharacterSummary(BaseModel):
    """Summary of a character for lists"""
    id: int
    name: str
    description: str
    universe: Optional[str] = None

    class Config:
        from_attributes = True


class CharacterState(BaseModel):
    """Current state of a character in a session"""
    character_id: int
    mood: str = Field("neutral",
                      description="Current mood of the character",
                      pattern="^(cheerful|friendly|neutral|annoyed|angry)$")
    current_context: dict[str, Any] = Field(default_factory=dict,
                                            description="Current context of the conversation")
    recent_memories: list[dict[str, Any]] = Field(default_factory=list,
                                                  description="Recent memories")
    relationship_to_user: dict[str, Any] = Field(
        default_factory=lambda: {"sentiment": 0.0,
                                 "trust": 0.0, "familiarity": 0.0},
        description="State of the relationship with the user"
    )
    active_traits: Optional[dict[str, float]] = Field(
        default_factory=dict,
        description="Active personality traits with their current values"
    )

    @validator('mood')
    def mood_must_be_valid(cls, v):
        valid_moods = ["cheerful", "friendly", "neutral", "annoyed", "angry"]
        if v not in valid_moods:
            raise ValueError(
                f'Invalid mood. Accepted values: {", ".join(valid_moods)}')
        return v

    class Config:
        from_attributes = True


class TraitChange(BaseModel):
    """Represents a change in a personality trait"""
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

    class Config:
        from_attributes = True
