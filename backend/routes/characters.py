"""
Routes pour la gestion des personnages
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Optional

from models.character import Character, CharacterCreate, CharacterSummary
from services.character_manager import character_manager

router = APIRouter(prefix="/characters", tags=["characters"])


@router.post("/", response_model=dict)
async def create_character(character: CharacterCreate):
    """Crée un nouveau personnage"""
    try:
        character_id = character_manager.create_character(character)
        return {"id": character_id, "message": f"Personnage '{character.name}' créé avec succès"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la création du personnage: {str(e)}")


@router.get("/", response_model=List[CharacterSummary])
async def get_characters(limit: Optional[int] = Query(None, description="Limite le nombre de personnages retournés")):
    """Récupère tous les personnages"""
    try:
        characters = character_manager.get_characters(limit=limit)
        return characters
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la récupération des personnages: {str(e)}")


@router.get("/{character_id}", response_model=Character)
async def get_character(character_id: int = Path(..., description="ID du personnage")):
    """Récupère un personnage par son ID"""
    character = character_manager.get_character(character_id)
    if not character:
        raise HTTPException(
            status_code=404, detail=f"Personnage avec l'ID {character_id} non trouvé")
    return character


@router.delete("/{character_id}", response_model=dict)
async def delete_character(character_id: int = Path(..., description="ID du personnage")):
    """Supprime un personnage"""
    result = character_manager.delete_character(character_id)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Personnage avec l'ID {character_id} non trouvé")
    return {"message": f"Personnage avec l'ID {character_id} supprimé avec succès"}
