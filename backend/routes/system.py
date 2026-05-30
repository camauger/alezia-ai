"""
Routes for system functions
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import inspect

from backend.database import engine
from backend.services.llm_service import llm_service

router = APIRouter(prefix='/system', tags=['system'])


@router.get('/check-database', response_model=dict[str, Any])
async def check_database():
    """Checks the database status via SQLAlchemy."""
    try:
        tables = inspect(engine).get_table_names()
        return {'status': 'ok', 'tables': tables, 'database_path': str(engine.url)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')


@router.get('/check-llm', response_model=dict[str, Any])
async def check_llm():
    """Checks the LLM service status"""
    try:
        status = llm_service.check_model_availability()
        return {'status': 'ok' if status else 'error'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'LLM service error: {str(e)}')
