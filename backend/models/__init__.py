"""
Package des modèles de données pour l'application
"""

from .character import Character, CharacterCreate, CharacterSummary, CharacterState
from .memory import Memory, MemoryCreate, RetrievedMemory, Fact, FactCreate
from .universe import Universe, UniverseCreate, UniverseElement, UniverseElementCreate, UniverseSummary, UniverseDetail
from .relationship import Relationship, RelationshipCreate, RelationshipUpdate, UserCharacterRelationship

__all__ = [
    'Character', 'CharacterCreate', 'CharacterSummary', 'CharacterState',
    'Memory', 'MemoryCreate', 'RetrievedMemory', 'Fact', 'FactCreate',
    'Universe', 'UniverseCreate', 'UniverseElement', 'UniverseElementCreate', 'UniverseSummary', 'UniverseDetail',
    'Relationship', 'RelationshipCreate', 'RelationshipUpdate', 'UserCharacterRelationship'
]
