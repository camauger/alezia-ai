"""
Module for universe models and their elements
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class UniverseModel(Base):
    __tablename__ = "universes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    type = Column(String)
    time_period = Column(String, nullable=True)
    rules = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    characters = relationship("CharacterModel", back_populates="universe")
    elements = relationship("UniverseElementModel", back_populates="universe")

class UniverseElementModel(Base):
    __tablename__ = "universe_elements"

    id = Column(Integer, primary_key=True, index=True)
    universe_id = Column(Integer, ForeignKey("universes.id"))
    name = Column(String)
    type = Column(String)
    description = Column(Text)
    importance = Column(Integer, default=3)

    universe = relationship("UniverseModel", back_populates="elements")

# Pydantic models

class UniverseBase(BaseModel):
    """Base model for universes"""
    name: str = Field(..., description="Name of the universe")
    description: str = Field(..., description="General description of the universe")
    type: str = Field(..., description="Type of universe (fantasy, sci-fi, historical, etc.)")
    time_period: Optional[str] = Field(None, description="Specific time period")
    rules: Optional[str] = Field(None, description="Particular rules of this universe")


class UniverseCreate(UniverseBase):
    """Model for creating a universe"""
    pass


class Universe(UniverseBase):
    """Complete model of a universe with its metadata"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UniverseElementBase(BaseModel):
    """Base model for universe elements"""
    universe_id: int = Field(..., description="ID of the universe this element belongs to")
    name: str = Field(..., description="Name of the element")
    type: str = Field(..., description="Type of element (location, organization, item, concept, etc.)")
    description: str = Field(..., description="Detailed description of the element")
    importance: int = Field(3, description="Importance of the element in the universe (1-5)")


class UniverseElementCreate(UniverseElementBase):
    """Model for creating a universe element"""
    pass


class UniverseElement(UniverseElementBase):
    """Complete model of a universe element with its metadata"""
    id: int

    class Config:
        from_attributes = True


class UniverseSummary(BaseModel):
    """Summary of a universe for lists"""
    id: int
    name: str
    type: str
    time_period: Optional[str] = None
    character_count: int = 0

    class Config:
        from_attributes = True


class UniverseDetail(Universe):
    """Complete details of a universe with its elements"""
    elements: list[UniverseElement] = []
    characters: list[dict] = []

    class Config:
        from_attributes = True
