"""
Package des modèles de données pour l'application
"""

from .character import Character, CharacterCreate, CharacterState, CharacterSummary
from .memory import Fact, FactCreate, Memory, MemoryCreate, RetrievedMemory
from .relationship import (
    Relationship,
    RelationshipCreate,
    RelationshipUpdate,
    UserCharacterRelationship,
)
from .universe import (
    Universe,
    UniverseCreate,
    UniverseDetail,
    UniverseElement,
    UniverseElementCreate,
    UniverseSummary,
)

__all__ = [
    'Character',
    'CharacterCreate',
    'CharacterSummary',
    'CharacterState',
    'Memory',
    'MemoryCreate',
    'RetrievedMemory',
    'Fact',
    'FactCreate',
    'Universe',
    'UniverseCreate',
    'UniverseElement',
    'UniverseElementCreate',
    'UniverseSummary',
    'UniverseDetail',
    'Relationship',
    'RelationshipCreate',
    'RelationshipUpdate',
    'UserCharacterRelationship',
]
