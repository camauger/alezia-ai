"""
Routes pour la gestion des sessions de chat et des messages
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from services.chat_manager import chat_manager

router = APIRouter(prefix="/chat", tags=["Chat"])


class MessageCreate(BaseModel):
    """Modèle pour la création d'un message"""
    content: str


class SessionCreate(BaseModel):
    """Modèle pour la création d'une session"""
    character_id: int


@router.post("/session", status_code=201)
@router.post("/session/", status_code=201)
async def create_session(session: SessionCreate) -> Dict[str, Any]:
    """Crée une nouvelle session de chat"""
    try:
        result = chat_manager.create_session(session.character_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/session/{session_id}")
@router.get("/session/{session_id}/")
async def get_session(session_id: int) -> Dict[str, Any]:
    """Récupère les détails d'une session"""
    session = chat_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return session


@router.get("/character/{character_id}/sessions")
@router.get("/character/{character_id}/sessions/")
async def get_character_sessions(character_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Récupère les sessions pour un personnage"""
    return chat_manager.get_character_sessions(character_id, limit)


@router.post("/{session_id}/message")
@router.post("/{session_id}/message/")
async def send_message(session_id: int, message: MessageCreate) -> Dict[str, Any]:
    """Envoie un message dans la session et génère une réponse"""
    try:
        result = await chat_manager.send_message(session_id, message.content)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/history")
@router.get("/{session_id}/history/")
async def get_session_history(session_id: int) -> Dict[str, Any]:
    """Récupère l'historique d'une session"""
    session = chat_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return session


@router.post("/{session_id}/end", status_code=200)
@router.post("/{session_id}/end/", status_code=200)
async def end_session(session_id: int) -> Dict[str, bool]:
    """Termine une session de chat"""
    success = chat_manager.end_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"success": True}
