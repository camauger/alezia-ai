"""
Module for relationship models between characters
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class RelationshipModel(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    target_name = Column(String)
    sentiment = Column(Float, default=0.0)
    trust = Column(Float, default=0.0)
    familiarity = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    last_updated = Column(DateTime, default=datetime.now)

    character = relationship("CharacterModel", back_populates="relationships")

# Pydantic models

class RelationshipBase(BaseModel):
    """Base model for relationships"""
    character_id: int = Field(..., description="ID of the source character of the relationship")
    target_name: str = Field(..., description="Name of the target character or entity")
    sentiment: float = Field(0.0, description="General sentiment (-1.0 negative to 1.0 positive)")
    trust: float = Field(0.0, description="Level of trust (0.0 to 1.0)")
    familiarity: float = Field(0.0, description="Level of familiarity (0.0 to 1.0)")
    notes: Optional[str] = Field(None, description="Additional notes on the relationship")


class RelationshipCreate(RelationshipBase):
    """Model for creating a relationship"""
    pass


class Relationship(RelationshipBase):
    """Complete model of a relationship with its metadata"""
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


class RelationshipUpdate(BaseModel):
    """Model for updating a relationship"""
    sentiment: Optional[float] = None
    trust: Optional[float] = None
    familiarity: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class UserCharacterRelationship(BaseModel):
    """Specific relationship between the user and a character"""
    character_id: int
    username: str = "user"  # By default, we simply use "user"
    sentiment: float = 0.0
    trust: float = 0.0
    familiarity: float = 0.0
    interactions_count: int = 0
    last_interaction: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
