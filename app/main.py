import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1 import api_router
from app.db.events import create_start_app_handler, create_stop_app_handler
from app.core.middleware import RequestLoggingMiddleware, PerformanceMonitoringMiddleware
from app.core.logger import Logger, logger
from app.core.error_handler import register_exception_handlers
import logging
import time

def create_folders():
    """Create necessary folders for application"""
    try:
        # Create logs directory if it doesn't exist
        if settings.LOG_TO_FILE and not os.path.exists(settings.LOG_DIR):
            os.makedirs(settings.LOG_DIR)
            logger.info(f"Created log directory: {settings.LOG_DIR}")

        # Create any other required directories here
        # e.g., uploads, temp directories, etc.
    except Exception as e:
        logger.critical(f"Failed to create required directories: {str(e)}")
        raise

def setup_middleware(app: FastAPI) -> None:
    """Configure middleware for the application"""
    try:
        # CORS middleware
        if settings.BACKEND_CORS_ORIGINS:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            logger.info("CORS middleware configured", extra={
                "origins": settings.BACKEND_CORS_ORIGINS
            })

        # Request logging middleware
        app.add_middleware(RequestLoggingMiddleware)
        logger.info("Request logging middleware configured")

        # Performance monitoring middleware
        app.add_middleware(PerformanceMonitoringMiddleware)
        logger.info("Performance monitoring middleware configured")

    except Exception as e:
        logger.critical("Failed to setup middleware", extra={"error": str(e)})
        raise

def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    try:
        # Initialize logger before app creation
        Logger.setup_uvicorn_logging()
        logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
        
        # Create required folders
        create_folders()

        # Initialize FastAPI application
        application = FastAPI(
            title=settings.PROJECT_NAME,
            version=settings.VERSION,
            description="Glutt.ai API with MongoDB",
            openapi_url=f"{settings.API_V1_STR}/openapi.json",
        )
        logger.info("FastAPI application initialized")

        # Setup middleware
        setup_middleware(application)

        # Register exception handlers
        register_exception_handlers(application)
        logger.info("Exception handlers registered")

        # Add event handlers
        application.add_event_handler(
            "startup",
            create_start_app_handler(application)
        )
        application.add_event_handler(
            "shutdown",
            create_stop_app_handler(application)
        )
        logger.info("Application event handlers registered")

        # Include routers
        application.include_router(api_router, prefix=settings.API_V1_STR)
        logger.info(f"API router mounted at {settings.API_V1_STR}")

        @application.get("/health", tags=["health"])
        async def health_check(request: Request):
            """Health check endpoint with basic diagnostics"""
            start_time = time.time()
            
            # Collect health metrics
            health_info = {
                "status": "healthy",
                "timestamp": time.time(),
                "version": settings.VERSION,
                "environment": os.getenv("ENV", "development")
            }
            
            # Add response time
            health_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
            
            logger.debug("Health check performed", extra=health_info)
            return health_info

        @application.get("/", tags=["root"])
        async def root():
            """Root endpoint"""
            return {
                "application": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "status": "running"
            }

        logger.info("Application startup complete")
        return application

    except Exception as e:
        logger.critical("Failed to create application", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise

# Create the application instance
try:
    app = create_application()
    logger.info("Application instance created successfully")
except Exception as e:
    logger.critical("Fatal error during application creation", extra={
        "error": str(e),
        "error_type": type(e).__name__
    })
    raise

# Startup message
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting application server on http://localhost:8000")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )