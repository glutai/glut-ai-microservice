# app/core/logger.py
import logging
import sys
import os
import json
from datetime import datetime
import time
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from app.core.config import settings

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        logging.DEBUG: "\033[36m",    # CYAN
        logging.INFO: "\033[32m",     # GREEN
        logging.WARNING: "\033[33m",  # YELLOW
        logging.ERROR: "\033[31m",    # RED
        logging.CRITICAL: "\033[41m", # RED BACKGROUND
    }

    def format(self, record: Any) -> str:
        if hasattr(record, 'color') and not record.color:
            return super().format(record)
            
        if record.levelno in self.COLORS:
            color = self.COLORS[record.levelno]
            reset = "\033[0m"
            record.levelname = f"{color}{record.levelname}{reset}"
            record.msg = f"{color}{record.msg}{reset}"
        return super().format(record)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: Any) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line_number": record.lineno,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        # Add extra attributes if available
        if hasattr(record, 'extra') and record.extra:
            log_data.update(record.extra)
            
        return json.dumps(log_data)

class Logger:
    """Enhanced logger class with multiple output options"""
    
    _loggers: Dict[str, logging.Logger] = {}
    
    @classmethod
    def get_logger(cls, name: str = "fastapi_app") -> logging.Logger:
        """Get or create a logger instance with the given name"""
        if name in cls._loggers:
            return cls._loggers[name]
            
        logger = logging.getLogger(name)
        
        # Set the log level from settings
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
            
        # Console handler
        if settings.LOG_TO_CONSOLE:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            
            # Format for console
            formatter = CustomFormatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if settings.LOG_TO_FILE:
            # Create log directory if it doesn't exist
            os.makedirs(settings.LOG_DIR, exist_ok=True)
            
            # Create file handler based on rotation configuration
            if settings.LOG_ROTATION_TYPE == "size":
                file_handler = RotatingFileHandler(
                    filename=os.path.join(settings.LOG_DIR, f"{name}.log"),
                    maxBytes=settings.LOG_MAX_SIZE,
                    backupCount=settings.LOG_BACKUP_COUNT
                )
            else:  # time-based rotation
                file_handler = TimedRotatingFileHandler(
                    filename=os.path.join(settings.LOG_DIR, f"{name}.log"),
                    when=settings.LOG_ROTATION_WHEN,
                    interval=settings.LOG_ROTATION_INTERVAL,
                    backupCount=settings.LOG_BACKUP_COUNT
                )
                
            file_handler.setLevel(log_level)
            
            # Use JSON formatter for file logs if configured
            if settings.LOG_FORMAT == "json":
                formatter = JSONFormatter()
            else:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
                
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        # Store and return logger
        cls._loggers[name] = logger
        return logger
        
    @classmethod
    def setup_uvicorn_logging(cls):
        """Configure Uvicorn's logging to match our format"""
        for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
            log = logging.getLogger(logger_name)
            log.handlers = []  # Remove default handlers
            
            # Add our handlers
            logger = cls.get_logger(logger_name)
            for handler in logger.handlers:
                log.addHandler(handler)

# Extend the built-in logging.Logger class with timing methods
def add_timing_methods(logger):
    def debug_timing(self, operation_name):
        """Start timing an operation, returns the start time"""
        start_time = time.time()
        self.debug(f"Starting operation: {operation_name}")
        return start_time
        
    def debug_timing_end(self, start_time, operation_name):
        """End timing an operation and log the duration"""
        duration_ms = (time.time() - start_time) * 1000
        self.debug(f"Completed operation: {operation_name} in {round(duration_ms, 2)}ms")
        return duration_ms
        
    # Add methods to logger class
    logging.Logger.debug_timing = debug_timing
    logging.Logger.debug_timing_end = debug_timing_end
    return logger

# Create a default application logger
logger = add_timing_methods(Logger.get_logger("app"))

# Create specialized loggers for different components
db_logger = add_timing_methods(Logger.get_logger("app.db"))
api_logger = add_timing_methods(Logger.get_logger("app.api"))
service_logger = add_timing_methods(Logger.get_logger("app.service"))