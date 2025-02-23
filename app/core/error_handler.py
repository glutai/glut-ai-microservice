from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.errors import NotFoundError, ValidationError, DatabaseError, AuthenticationError
from app.core.logger import logger
import traceback

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors from FastAPI"""
    error_detail = exc.errors()
    logger.warning(
        "Validation error",
        extra={
            "request_path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "errors": error_detail
        }
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation Error",
            "errors": error_detail
        }
    )

async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """Handle not found errors"""
    logger.info(
        f"Not found: {exc.detail}",
        extra={
            "request_path": request.url.path,
            "client_ip": request.client.host if request.client else None
        }
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "message": exc.detail
        }
    )

async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors"""
    logger.warning(
        f"Authentication error: {exc.detail}",
        extra={
            "request_path": request.url.path,
            "client_ip": request.client.host if request.client else None
        }
    )
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "success": False,
            "message": exc.detail
        },
        headers={"WWW-Authenticate": "Bearer"}
    )

async def database_exception_handler(request: Request, exc: DatabaseError):
    """Handle database errors"""
    logger.error(
        f"Database error: {exc.detail}",
        extra={
            "request_path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "error": str(exc)
        }
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Database operation failed"
        }
    )

async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    logger.warning(
        f"Validation error: {exc.detail}",
        extra={
            "request_path": request.url.path,
            "client_ip": request.client.host if request.client else None
        }
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": exc.detail
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    # Get full traceback
    error_traceback = traceback.format_exc()
    
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "request_path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "error_type": type(exc).__name__,
            "error_traceback": error_traceback
        }
    )
    
    # In production, don't return the actual error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected error occurred"
        }
    )

def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app"""
    # Register specific exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(NotFoundError, not_found_exception_handler)
    app.add_exception_handler(AuthenticationError, authentication_exception_handler)
    app.add_exception_handler(DatabaseError, database_exception_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    
    # Register general exception handler for unhandled exceptions
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("All exception handlers registered")