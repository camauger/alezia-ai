"""
Routes pour les fonctions système
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from utils.db import db_manager
from services.llm_service import llm_service

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/check-database", response_model=Dict[str, Any])
async def check_database():
    """Vérifie l'état de la base de données"""
    try:
        # Vérifier que nous pouvons exécuter une requête simple
        results = db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row.get("name") for row in results]

        return {
            "status": "ok",
            "tables": tables,
            "database_path": str(db_manager.db_path)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur de base de données: {str(e)}")


@router.get("/check-llm", response_model=Dict[str, Any])
async def check_llm():
    """Vérifie l'état du service LLM"""
    try:
        status = await llm_service.check_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur du service LLM: {str(e)}")
