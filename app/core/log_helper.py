from functools import wraps
import time
import inspect
from typing import Any, Callable, Dict
from app.core.logger import logger

def log_function_call(func: Callable) -> Callable:
    """Decorator to log function calls with timing"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Get function details
        func_name = func.__name__
        module_name = func.__module__
        
        try:
            # Log function entry
            logger.debug(f"Entering {func_name}", extra={
                "module": module_name,
                "function": func_name,
                "args_length": len(args),
                "kwargs_keys": list(kwargs.keys())
            })
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful completion
            logger.debug(
                f"Completed {func_name}",
                extra={
                    "module": module_name,
                    "function": func_name,
                    "duration_ms": round(duration_ms, 2)
                }
            )
            
            return result
            
        except Exception as e:
            # Log error with context
            logger.error(
                f"Error in {func_name}",
                extra={
                    "module": module_name,
                    "function": func_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": round((time.time() - start_time) * 1000, 2)
                }
            )
            raise
            
    return wrapper

def log_database_query(operation: str) -> Callable:
    """Decorator specifically for database operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Get query details if possible
            query_info = kwargs.get('query', kwargs.get('filter', {}))
            
            try:
                # Log query start
                logger.debug(f"Database {operation} started", extra={
                    "operation": operation,
                    "collection": getattr(args[0], 'collection_name', 'unknown'),
                    "query": str(query_info)
                })
                
                # Execute query
                result = await func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log successful query
                logger.debug(
                    f"Database {operation} completed",
                    extra={
                        "operation": operation,
                        "duration_ms": round(duration_ms, 2),
                        "result_type": type(result).__name__
                    }
                )
                
                return result
                
            except Exception as e:
                # Log database error
                logger.error(
                    f"Database {operation} failed",
                    extra={
                        "operation": operation,
                        "error": str(e),
                        "query": str(query_info),
                        "duration_ms": round((time.time() - start_time) * 1000, 2)
                    }
                )
                raise
                
        return wrapper
    return decorator

def log_business_logic(operation: str) -> Callable:
    """Decorator for business logic operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Clean sensitive data from args
            safe_args = {
                k: v for k, v in bound_args.arguments.items() 
                if k not in ['password', 'token', 'secret']
            }
            
            try:
                # Log operation start
                logger.info(f"Business operation '{operation}' started", extra={
                    "operation": operation,
                    "function": func.__name__,
                    "parameters": safe_args
                })
                
                # Execute operation
                result = await func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log successful operation
                logger.info(
                    f"Business operation '{operation}' completed",
                    extra={
                        "operation": operation,
                        "duration_ms": round(duration_ms, 2),
                        "success": True
                    }
                )
                
                return result
                
            except Exception as e:
                # Log business error
                logger.error(
                    f"Business operation '{operation}' failed",
                    extra={
                        "operation": operation,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration_ms": round((time.time() - start_time) * 1000, 2)
                    }
                )
                raise
                
        return wrapper
    return decorator

def log_api_call(endpoint: str) -> Callable:
    """Decorator for API endpoint calls"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Clean sensitive data
            safe_kwargs = {
                k: v for k, v in kwargs.items() 
                if k not in ['password', 'token', 'secret']
            }
            
            try:
                # Log API call
                logger.info(f"API endpoint '{endpoint}' called", extra={
                    "endpoint": endpoint,
                    "parameters": safe_kwargs
                })
                
                # Execute endpoint
                result = await func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log successful call
                logger.info(
                    f"API endpoint '{endpoint}' completed",
                    extra={
                        "endpoint": endpoint,
                        "duration_ms": round(duration_ms, 2),
                        "status": "success"
                    }
                )
                
                return result
                
            except Exception as e:
                # Log API error
                logger.error(
                    f"API endpoint '{endpoint}' failed",
                    extra={
                        "endpoint": endpoint,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration_ms": round((time.time() - start_time) * 1000, 2)
                    }
                )
                raise
                
        return wrapper
    return decorator

def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Utility function to remove sensitive information from log data"""
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'api_key', 'authorization',
        'access_token', 'refresh_token', 'private_key', 'secret_key'
    }
    
    def _sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for k, v in d.items():
            if any(sensitive in k.lower() for sensitive in SENSITIVE_FIELDS):
                sanitized[k] = '***REDACTED***'
            elif isinstance(v, dict):
                sanitized[k] = _sanitize_dict(v)
            elif isinstance(v, list):
                sanitized[k] = [_sanitize_dict(i) if isinstance(i, dict) else i for i in v]
            else:
                sanitized[k] = v
        return sanitized
    
    return _sanitize_dict(data)