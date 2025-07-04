"""
Module de gestion des erreurs pour l'application
Fournit des exceptions personnalisées et des handlers pour l'API
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


# Exceptions personnalisées
class AleziaBaseException(Exception):
    """Exception de base pour l'application"""

    def __init__(
        self, message='Une erreur est survenue', status_code=500, details=None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundException(AleziaBaseException):
    """Exception levée lorsqu'une ressource n'est pas trouvée"""

    def __init__(self, resource_type, resource_id, message=None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(
            message or f"{resource_type} avec l'ID {resource_id} non trouvé",
            status_code=404,
            details={'resource_type': resource_type, 'resource_id': resource_id},
        )


class DatabaseException(AleziaBaseException):
    """Exception levée lors d'erreurs de base de données"""

    def __init__(
        self, message='Erreur de base de données', operation=None, details=None
    ):
        super().__init__(
            message,
            status_code=500,
            details={'operation': operation, **(details or {})},
        )


class ValidationException(AleziaBaseException):
    """Exception levée lors d'erreurs de validation"""

    def __init__(self, message='Données invalides', field=None, error=None):
        super().__init__(
            message, status_code=422, details={'field': field, 'error': error}
        )


class LLMServiceException(AleziaBaseException):
    """Exception levée lors d'erreurs avec le service LLM"""

    def __init__(self, message='Erreur du service LLM', model=None, details=None):
        super().__init__(
            message,
            status_code=503,  # Service Unavailable
            details={'model': model, **(details or {})},
        )


# Gestionnaires d'exceptions pour FastAPI
def configure_exception_handlers(app: FastAPI):
    """Configure les gestionnaires d'exceptions pour l'application FastAPI"""

    @app.exception_handler(AleziaBaseException)
    async def alezia_exception_handler(request: Request, exc: AleziaBaseException):
        """Gestionnaire pour les exceptions de base Alezia"""
        logger.error(f'Exception Alezia: {exc.message} - {exc.details}')
        return JSONResponse(
            status_code=exc.status_code,
            content={'success': False, 'error': exc.message, 'details': exc.details},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Gestionnaire pour les erreurs de validation FastAPI"""
        errors = []
        for error in exc.errors():
            field = '.'.join([str(loc) for loc in error['loc'][1:]])
            errors.append(
                {'field': field, 'message': error['msg'], 'type': error['type']}
            )

        logger.warning(f'Erreur de validation: {errors}')
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'success': False,
                'error': 'Erreur de validation des données',
                'details': {'errors': errors},
            },
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ):
        """Gestionnaire pour les erreurs de validation Pydantic"""
        errors = []
        for error in exc.errors():
            field = '.'.join([str(loc) for loc in error['loc']])
            errors.append(
                {'field': field, 'message': error['msg'], 'type': error['type']}
            )

        logger.warning(f'Erreur de validation Pydantic: {errors}')
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'success': False,
                'error': 'Erreur de validation des données',
                'details': {'errors': errors},
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Gestionnaire pour les exceptions non gérées"""
        logger.exception(f'Exception non gérée: {str(exc)}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'success': False,
                'error': 'Erreur interne du serveur',
                'details': {'type': exc.__class__.__name__, 'message': str(exc)},
            },
        )
