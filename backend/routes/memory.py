"""
Routes pour la gestion des mémoires
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
import logging

from backend.services.memory_manager import memory_manager
from backend.models.memory import Memory, Fact, RetrievedMemory, MemoryCreate

router = APIRouter(prefix="/memory", tags=["Memory"])
logger = logging.getLogger(__name__)


@router.get("/character/{character_id}/memories")
@router.get("/character/{character_id}/memories/")
async def get_character_memories(character_id: int, limit: int = 100) -> List[Memory]:
    """
    Récupère les mémoires d'un personnage
    """
    memories = memory_manager.get_memories(character_id, limit)
    return memories


@router.get("/character/{character_id}/facts")
@router.get("/character/{character_id}/facts/")
async def get_character_facts(character_id: int, subject: Optional[str] = None) -> List[Fact]:
    """
    Récupère les faits extraits des mémoires d'un personnage
    """
    facts = memory_manager.get_facts(character_id, subject)
    return facts


@router.post("/character/{character_id}/memories")
@router.post("/character/{character_id}/memories/")
async def create_memory(character_id: int, memory: MemoryCreate) -> Dict[str, Any]:
    """
    Crée une nouvelle mémoire pour un personnage
    """
    if memory.character_id != character_id:
        raise HTTPException(
            status_code=400,
            detail="L'ID du personnage ne correspond pas à celui spécifié dans l'URL"
        )

    try:
        memory_id = memory_manager.create_memory(memory)
        return {"id": memory_id, "success": True}
    except Exception as e:
        logger.error(f"Erreur lors de la création de la mémoire: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories/{memory_id}")
@router.get("/memories/{memory_id}/")
async def get_memory(memory_id: int) -> Memory:
    """
    Récupère une mémoire spécifique
    """
    memory = memory_manager.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Mémoire introuvable")
    return memory


@router.put("/memories/{memory_id}/importance")
@router.put("/memories/{memory_id}/importance/")
async def update_memory_importance(memory_id: int, importance: float = Body(..., embed=True)) -> Dict[str, Any]:
    """
    Met à jour l'importance d'une mémoire
    """
    # Limiter l'importance entre 0 et 10
    importance = max(0.0, min(10.0, importance))

    try:
        success = memory_manager.update_memory_importance(
            memory_id, importance)
        if not success:
            raise HTTPException(status_code=404, detail="Mémoire introuvable")
        return {"success": True, "importance": importance}
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de l'importance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memories/{memory_id}")
@router.delete("/memories/{memory_id}/")
async def delete_memory(memory_id: int) -> Dict[str, bool]:
    """
    Supprime une mémoire
    """
    success = memory_manager.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mémoire introuvable")
    return {"success": True}


@router.post("/character/{character_id}/maintenance")
@router.post("/character/{character_id}/maintenance/")
async def run_memory_maintenance(character_id: int) -> Dict[str, Any]:
    """
    Exécute un cycle de maintenance sur les mémoires d'un personnage
    """
    try:
        stats = memory_manager.maintenance_cycle(character_id)
        return {"success": True, "statistics": stats}
    except Exception as e:
        logger.error(f"Erreur lors du cycle de maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/character/{character_id}/relevant")
@router.get("/character/{character_id}/relevant/")
async def get_relevant_memories(
    character_id: int,
    query: str,
    limit: int = 5,
    recency_weight: float = Query(0.3, ge=0.0, le=1.0),
    importance_weight: float = Query(0.4, ge=0.0, le=1.0)
) -> List[RetrievedMemory]:
    """
    Récupère les mémoires les plus pertinentes pour une requête
    """
    try:
        memories = memory_manager.get_relevant_memories(
            character_id,
            query,
            limit,
            recency_weight,
            importance_weight
        )
        return memories
    except Exception as e:
        logger.error(
            f"Erreur lors de la recherche de mémoires pertinentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
