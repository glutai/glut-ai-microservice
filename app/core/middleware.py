import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.logger import logger
from app.core.config import settings
import json

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.info("Request logging middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timer for request duration
        start_time = time.time()
        
        # Prepare request details
        request_details = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "path_params": dict(request.path_params),
            "query_params": dict(request.query_params)
        }
        
        # Log headers if enabled
        if settings.LOG_REQUEST_HEADERS:
            request_details["headers"] = dict(request.headers)
            
        # Log request body for POST/PUT/PATCH if enabled
        if settings.LOG_REQUEST_BODY and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    content_type = request.headers.get("content-type", "")
                    if "application/json" in content_type:
                        request_details["body"] = json.loads(body.decode())
                    else:
                        request_details["body"] = "Binary or form data"
                    request._body = body  # Restore body for further processing
            except Exception as e:
                logger.warning(f"Failed to log request body: {str(e)}")
        
        # Log the incoming request
        logger.info(f"Incoming request: {request.method} {request.url.path}", 
                    extra={"request": request_details})
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Prepare response details
            response_details = {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2)
            }
            
            # Log response
            log_message = (f"Request completed: {request.method} {request.url.path} "
                           f"- {response.status_code} in {round(duration_ms, 2)}ms")
            
            # Log at appropriate level based on status code
            if response.status_code >= 500:
                logger.error(log_message, extra={
                    "response": response_details,
                    "request": request_details
                })
            elif response.status_code >= 400:
                logger.warning(log_message, extra={
                    "response": response_details
                })
            else:
                logger.info(log_message, extra={
                    "response": response_details
                })
            
            # Log slow requests
            if settings.LOG_SLOW_REQUESTS and duration_ms > settings.LOG_SLOW_THRESHOLD_MS:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path}",
                    extra={
                        "request_id": request_id,
                        "duration_ms": round(duration_ms, 2),
                        "threshold_ms": settings.LOG_SLOW_THRESHOLD_MS,
                        "request": request_details
                    }
                )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log unhandled exceptions
            logger.exception(
                f"Unhandled exception in request: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "request": request_details
                }
            )
            raise

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.info("Performance monitoring middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000

        # Log performance metrics
        logger.info("Request performance metrics", extra={
            "path": request.url.path,
            "method": request.method,
            "process_time_ms": round(process_time, 2),
            "status_code": response.status_code
        })

        return response
    
class UserContextMiddleware(BaseHTTPMiddleware):
    """Extract user context from upstream service headers"""
    
    async def dispatch(self, request: Request, call_next):
        # Extract user context from headers set by API gateway
        user_id = request.headers.get("X-User-ID")
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # Add to request state for use in handlers
        request.state.user_id = user_id
        request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        return response

