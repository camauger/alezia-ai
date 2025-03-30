"""
Routes pour la gestion des personnages
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Path, Query, Depends, Body
from pydantic import BaseModel, Field

from backend.models.character import Character, CharacterSummary, CharacterCreate, CharacterState
from backend.models.character import CharacterTrait, PersonalityTraits, TraitChange
from backend.services.character_manager import CharacterManager

router = APIRouter(prefix="/characters", tags=["Characters"])
logger = logging.getLogger(__name__)
character_manager = CharacterManager()


class TraitUpdateRequest(BaseModel):
    """Requête pour mettre à jour un trait de personnalité"""
    value: float = Field(..., ge=-1.0, le=1.0)
    reason: str = Field(..., min_length=3, max_length=200)


@router.get("/")
async def get_characters():
    """Récupère la liste des personnages"""
    try:
        characters = character_manager.get_characters()
        return characters
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des personnages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=201)
async def create_character(character: CharacterCreate):
    """Crée un nouveau personnage"""
    try:
        character_id = character_manager.create_character(character)
        return {"id": character_id, "message": "Personnage créé avec succès"}
    except Exception as e:
        logger.error(f"Erreur lors de la création du personnage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{character_id}")
async def get_character(character_id: int = Path(..., ge=1)):
    """Récupère les détails d'un personnage"""
    try:
        character = character_manager.get_character(character_id)
        if not character:
            raise HTTPException(
                status_code=404, detail=f"Personnage {character_id} introuvable")
        return character
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erreur lors de la récupération du personnage {character_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{character_id}")
async def delete_character(character_id: int = Path(..., ge=1)):
    """Supprime un personnage"""
    try:
        success = character_manager.delete_character(character_id)
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Personnage {character_id} introuvable")
        return {"message": "Personnage supprimé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erreur lors de la suppression du personnage {character_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{character_id}/state")
async def get_character_state(character_id: int = Path(..., ge=1)):
    """Récupère l'état actuel d'un personnage"""
    try:
        state = character_manager.get_character_state(character_id)
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"Erreur lors de la récupération de l'état du personnage {character_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{character_id}/traits")
async def get_character_traits(character_id: int = Path(..., ge=1)):
    """Récupère les traits de personnalité d'un personnage"""
    try:
        traits = character_manager.get_personality_traits(character_id)
        return traits
    except Exception as e:
        logger.error(
            f"Erreur lors de la récupération des traits du personnage {character_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{character_id}/traits/history")
async def get_trait_history(
    character_id: int = Path(..., ge=1),
    trait_name: Optional[str] = Query(
        None, description="Nom du trait spécifique à consulter")
):
    """Récupère l'historique des changements de traits d'un personnage"""
    try:
        history = character_manager.get_trait_history(character_id, trait_name)
        return history
    except Exception as e:
        logger.error(
            f"Erreur lors de la récupération de l'historique des traits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{character_id}/traits/{trait_name}")
async def update_character_trait(
    character_id: int = Path(..., ge=1),
    trait_name: str = Path(..., min_length=2, max_length=50),
    update: TraitUpdateRequest = Body(...)
):
    """Met à jour un trait de personnalité"""
    try:
        success = character_manager.update_trait(
            character_id,
            trait_name,
            update.value,
            update.reason
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Trait {trait_name} introuvable pour le personnage {character_id}"
            )

        return {
            "message": f"Trait {trait_name} mis à jour avec succès",
            "new_value": update.value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erreur lors de la mise à jour du trait {trait_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
