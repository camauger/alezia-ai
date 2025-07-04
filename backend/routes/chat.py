"""
Routes pour la gestion des conversations
"""

import logging

from fastapi import APIRouter, HTTPException

from backend.models.chat import MessageCreate, SessionCreate
from backend.services.chat_service import chat_service

router = APIRouter(prefix='/chat', tags=['chat'])
logger = logging.getLogger(__name__)


@router.post('/create', status_code=201)
async def create_chat_session(session_data: SessionCreate):
    """
    Crée une nouvelle session de chat
    """
    try:
        session = chat_service.create_session(
            user_id=session_data.user_id,
            character_id=session_data.character_id,
            context=session_data.context.model_dump() if session_data.context else None,
        )
        return session
    except Exception as e:
        logger.error(f'Erreur lors de la création de session: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/session/{session_id}')
async def get_chat_session(session_id: str):
    """
    Récupère les détails d'une session de chat
    """
    try:
        session = chat_service.get_session(session_id)
        return session
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'Erreur lors de la récupération de session: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/sessions')
async def get_user_sessions(user_id: str, limit: int = 10):
    """
    Récupère les sessions de chat d'un utilisateur
    """
    try:
        sessions = chat_service.get_user_sessions(user_id, limit)
        return sessions
    except Exception as e:
        logger.error(f'Erreur lors de la récupération des sessions: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/message')
async def send_message(message_data: MessageCreate):
    """
    Envoie un message dans une session de chat et reçoit la réponse du personnage
    """
    try:
        # Envoyer le message et récupérer la réponse
        response = chat_service.send_message(
            session_id=message_data.session_id,
            user_input=message_data.content,
            metadata=message_data.metadata.model_dump()
            if message_data.metadata
            else None,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/messages/{session_id}')
async def get_session_messages(session_id: str, limit: int = 50, offset: int = 0):
    """
    Récupère les messages d'une session de chat
    """
    try:
        messages = chat_service.get_session_messages(session_id, limit, offset)
        return messages
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'Erreur lors de la récupération des messages: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/session/{session_id}')
async def delete_chat_session(session_id: str):
    """
    Supprime une session de chat
    """
    try:
        success = chat_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail='Session non trouvée')
        return {'message': 'Session supprimée avec succès'}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f'Erreur lors de la suppression de session: {e}')
        raise HTTPException(status_code=500, detail=str(e))
