"""
Modèles de données pour les conversations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationContext(BaseModel):
    """Contexte de conversation incluant le profil du personnage et les mémoires pertinentes"""
    character_profile: str = Field(
        description="Profil complet du personnage formaté pour le modèle"
    )
    recent_messages: Optional[List[Dict[str, Any]]] = Field(
        default=[],
        description="Messages récents de la conversation"
    )
    relevant_memories: Optional[List[Dict[str, Any]]] = Field(
        default=[],
        description="Mémoires pertinentes pour le contexte actuel"
    )
    system_instructions: Optional[str] = Field(
        default=None,
        description="Instructions système pour guider le modèle"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métadonnées additionnelles pour le contexte"
    )


class MessageMetadata(BaseModel):
    """Métadonnées pour un message"""
    generation_time: Optional[float] = Field(
        default=None,
        description="Temps de génération de la réponse en secondes"
    )
    model: Optional[str] = Field(
        default=None,
        description="Modèle utilisé pour générer la réponse"
    )
    tokens_used: Optional[int] = Field(
        default=None,
        description="Nombre de tokens utilisés pour générer la réponse"
    )
    custom_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Données personnalisées additionnelles"
    )


class MessageCreate(BaseModel):
    """Modèle pour la création d'un message"""
    session_id: str = Field(
        description="ID de la session de chat"
    )
    content: str = Field(
        description="Contenu du message"
    )
    metadata: Optional[MessageMetadata] = Field(
        default=None,
        description="Métadonnées du message"
    )


class ChatMessage(BaseModel):
    """Modèle pour un message de chat"""
    id: str = Field(
        description="ID unique du message"
    )
    session_id: str = Field(
        description="ID de la session de chat"
    )
    content: str = Field(
        description="Contenu du message"
    )
    sender: str = Field(
        description="Expéditeur du message (user ou assistant)"
    )
    character_id: Optional[int] = Field(
        default=None,
        description="ID du personnage (pour les messages de l'assistant)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Horodatage du message"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métadonnées du message"
    )


class SessionCreate(BaseModel):
    """Modèle pour la création d'une session"""
    character_id: int = Field(
        description="ID du personnage"
    )
    user_id: str = Field(
        description="ID de l'utilisateur"
    )
    context: Optional[ConversationContext] = Field(
        default=None,
        description="Contexte initial de la conversation"
    )


class ChatSession(BaseModel):
    """Modèle pour une session de chat"""
    id: str = Field(
        description="ID unique de la session"
    )
    user_id: str = Field(
        description="ID de l'utilisateur"
    )
    character_id: int = Field(
        description="ID du personnage"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de création de la session"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de dernière mise à jour de la session"
    )
    active: bool = Field(
        default=True,
        description="Indique si la session est active"
    )
    context: Optional[ConversationContext] = Field(
        default=None,
        description="Contexte de la conversation"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métadonnées de la session"
    )
