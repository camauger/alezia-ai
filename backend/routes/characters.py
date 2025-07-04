"""
Routes for character management
"""

import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.character import CharacterCreate
from backend.services.character_manager import character_manager

router = APIRouter(prefix='/characters', tags=['Characters'])
logger = logging.getLogger(__name__)


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TraitUpdateRequest(BaseModel):
    """Request to update a personality trait"""

    value: float = Field(..., ge=-1.0, le=1.0)
    reason: str = Field(..., min_length=3, max_length=200)


@router.get('/')
async def get_characters(db: Session = Depends(get_db)):
    """Retrieves the list of characters"""
    try:
        return character_manager.get_characters(db)
    except Exception as e:
        logger.error(f'Error retrieving characters: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/', status_code=201)
async def create_character(character: CharacterCreate, db: Session = Depends(get_db)):
    """Creates a new character"""
    try:
        character_id = character_manager.create_character(db, character)
        return {'id': character_id, 'message': 'Character created successfully'}
    except Exception as e:
        logger.error(f'Error creating character: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{character_id}')
async def get_character(
    character_id: int = Path(..., ge=1), db: Session = Depends(get_db)
):
    """Retrieves the details of a character"""
    try:
        character = character_manager.get_character(db, character_id)
        if not character:
            raise HTTPException(
                status_code=404, detail=f'Character {character_id} not found'
            )
        return character
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error retrieving character {character_id}: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/{character_id}')
async def delete_character(
    character_id: int = Path(..., ge=1), db: Session = Depends(get_db)
):
    """Deletes a character"""
    try:
        success = character_manager.delete_character(db, character_id)
        if not success:
            raise HTTPException(
                status_code=404, detail=f'Character {character_id} not found'
            )
        return {'message': 'Character deleted successfully'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error deleting character {character_id}: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{character_id}/state')
async def get_character_state(
    character_id: int = Path(..., ge=1), db: Session = Depends(get_db)
):
    """Retrieves the current state of a character"""
    try:
        return character_manager.get_character_state(db, character_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'Error retrieving character state {character_id}: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{character_id}/traits')
async def get_character_traits(
    character_id: int = Path(..., ge=1), db: Session = Depends(get_db)
):
    """Retrieves the personality traits of a character"""
    try:
        return character_manager.get_personality_traits(db, character_id)
    except Exception as e:
        logger.error(f'Error retrieving character traits {character_id}: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{character_id}/traits/history')
async def get_trait_history(
    character_id: int = Path(..., ge=1),
    trait_name: Optional[str] = Query(
        None, description='Name of the specific trait to consult'
    ),
    db: Session = Depends(get_db),
):
    """Retrieves the history of trait changes for a character"""
    try:
        return character_manager.get_trait_history(db, character_id, trait_name)
    except Exception as e:
        logger.error(f'Error retrieving trait history: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/{character_id}/traits/{trait_name}')
async def update_character_trait(
    character_id: int = Path(..., ge=1),
    trait_name: str = Path(..., min_length=2, max_length=50),
    update: TraitUpdateRequest = Body(...),
    db: Session = Depends(get_db),
):
    """Updates a personality trait"""
    try:
        success = character_manager.update_trait(
            db, character_id, trait_name, update.value, update.reason
        )
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f'Trait {trait_name} not found for character {character_id}',
            )
        return {
            'message': f'Trait {trait_name} updated successfully',
            'new_value': update.value,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error updating trait {trait_name}: {e}')
        raise HTTPException(status_code=500, detail=str(e))
