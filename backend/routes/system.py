"""
Routes for system functions
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.services.llm_service import llm_service
from backend.utils.db import db_manager

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/check-database", response_model=dict[str, Any])
async def check_database():
    """Checks the database status"""
    try:
        # Check that we can execute a simple query
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
            status_code=500, detail=f"Database error: {str(e)}")


@router.get("/check-llm", response_model=dict[str, Any])
async def check_llm():
    """Checks the LLM service status"""
    try:
        status = await llm_service.check_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"LLM service error: {str(e)}")
