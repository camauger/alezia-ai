"""
Routes for memory management
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Body, HTTPException, Query

from backend.models.memory import Fact, Memory, MemoryCreate, RetrievedMemory
from backend.services.memory_manager import memory_manager

router = APIRouter(prefix="/memory", tags=["Memory"])
logger = logging.getLogger(__name__)


@router.get("/character/{character_id}/memories")
@router.get("/character/{character_id}/memories/")
async def get_character_memories(character_id: int, limit: int = 100) -> list[Memory]:
    """
    Retrieves memories for a character
    """
    memories = memory_manager.get_memories(character_id, limit)
    return memories


@router.get("/character/{character_id}/facts")
@router.get("/character/{character_id}/facts/")
async def get_character_facts(character_id: int, subject: Optional[str] = None) -> list[Fact]:
    """
    Retrieves facts extracted from a character's memories
    """
    facts = memory_manager.get_facts(character_id, subject)
    return facts


@router.post("/character/{character_id}/memories")
@router.post("/character/{character_id}/memories/")
async def create_memory(character_id: int, memory: MemoryCreate) -> dict[str, Any]:
    """
    Creates a new memory for a character
    """
    if memory.character_id != character_id:
        raise HTTPException(
            status_code=400,
            detail="The character ID does not match the one specified in the URL"
        )

    try:
        memory_id = memory_manager.create_memory(memory)
        return {"id": memory_id, "success": True}
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories/{memory_id}")
@router.get("/memories/{memory_id}/")
async def get_memory(memory_id: int) -> Memory:
    """
    Retrieves a specific memory
    """
    memory = memory_manager.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.put("/memories/{memory_id}/importance")
@router.put("/memories/{memory_id}/importance/")
async def update_memory_importance(memory_id: int, importance: float = Body(..., embed=True)) -> dict[str, Any]:
    """
    Updates the importance of a memory
    """
    # Limit importance between 0 and 10
    importance = max(0.0, min(10.0, importance))

    try:
        success = memory_manager.update_memory_importance(
            memory_id, importance)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"success": True, "importance": importance}
    except Exception as e:
        logger.error(f"Error updating importance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memories/{memory_id}")
@router.delete("/memories/{memory_id}/")
async def delete_memory(memory_id: int) -> dict[str, bool]:
    """
    Deletes a memory
    """
    success = memory_manager.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"success": True}


@router.post("/character/{character_id}/maintenance")
@router.post("/character/{character_id}/maintenance/")
async def run_memory_maintenance(character_id: int) -> dict[str, Any]:
    """
    Runs a maintenance cycle on a character's memories
    """
    try:
        stats = memory_manager.maintenance_cycle(character_id)
        return {"success": True, "statistics": stats}
    except Exception as e:
        logger.error(f"Error during maintenance cycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/character/{character_id}/relevant")
@router.get("/character/{character_id}/relevant/")
async def get_relevant_memories(
    character_id: int,
    query: str,
    limit: int = 5,
    recency_weight: float = Query(0.3, ge=0.0, le=1.0),
    importance_weight: float = Query(0.4, ge=0.0, le=1.0)
) -> list[RetrievedMemory]:
    """
    Retrieves the most relevant memories for a query
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
            f"Error searching for relevant memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))
