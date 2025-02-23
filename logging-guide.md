# Logging System Guide

This document provides an overview of the logging system in the Glutt.ai API application.

## Overview

The application uses a structured logging system that provides:

- Colorized console output for development
- File-based logging with JSON format for production/analysis
- Request/response logging
- Performance monitoring
- Error tracking
- Specialized loggers for different components

## Configuration

Logging is configured through environment variables or the `.env` file:

```
# Logging level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Output formats
LOG_FORMAT=text  # text or json
LOG_TO_CONSOLE=true
LOG_TO_FILE=true
LOG_DIR=logs

# Rotation settings
LOG_ROTATION_TYPE=size  # size or time
LOG_MAX_SIZE=10485760  # 10MB
LOG_ROTATION_WHEN=midnight
LOG_ROTATION_INTERVAL=1
LOG_BACKUP_COUNT=5

# Request logging
LOG_REQUEST_DETAILS=true
LOG_RESPONSE_DETAILS=true
LOG_REQUEST_HEADERS=false  # Security consideration
LOG_REQUEST_BODY=false     # Security consideration

# Performance
LOG_SLOW_REQUESTS=true
LOG_SLOW_THRESHOLD_MS=500
```

## Logger Types

The application provides multiple specialized loggers:

- `logger` - General application logger
- `db_logger` - Database operations
- `api_logger` - API endpoints
- `service_logger` - Business logic services

## How to Use Logging

### Basic Logging

```python
from app.core.logger import logger

# Various log levels
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning: something unexpected")
logger.error("Error: something failed")
logger.critical("Critical: major failure")
```

### Structured Logging with Context

```python
# Add extra context to your logs
logger.info(
    "User action completed", 
    extra={
        "user_id": user.id,
        "action": "login",
        "ip_address": request.client.host
    }
)
```

### Performance Timing

```python
# Time an operation
start_time = logger.debug_timing("Database query")
# ... perform operation ...
logger.debug_timing_end(start_time, "Database query completed")
```

### Error Handling

```python
try:
    # Some operation
    result = await db.users.find_one({"_id": ObjectId(id)})
except Exception as e:
    logger.exception(f"Error retrieving user: {str(e)}")
    # or with context
    logger.error(
        "Failed to retrieve user",
        extra={
            "user_id": id,
            "error": str(e),
            "error_type": type(e).__name__
        }
    )
```

## Log Rotation

Logs are automatically rotated based on the configuration:

- Size-based: When a log file reaches the configured size
- Time-based: At specific time intervals (daily, hourly, etc.)

## Log Analysis

The JSON log format is designed to be easily parsed by log analysis tools like ELK Stack (Elasticsearch, Logstash, Kibana) or other log management systems.

## Best Practices

1. Use the appropriate log level:
   - DEBUG: Detailed information, typically of interest only when diagnosing problems
   - INFO: Confirmation that things are working as expected
   - WARNING: An indication that something unexpected happened, or a potential problem
   - ERROR: Due to a more serious problem, the software has not been able to perform some function
   - CRITICAL: A serious error, indicating that the program itself may be unable to continue running

2. Include relevant context in logs, but avoid sensitive information
3. Use structured logging with the `extra` parameter for better searchability
4. For slow operations, use the timing methods
5. Ensure all exceptions are properly logged
6. Don't log sensitive user data like passwords or tokens

## Specialized Loggers Usage

Each component should use its appropriate logger:

```python
# In database modules
from app.core.logger import db_logger as logger

# In API endpoints
from app.core.logger import api_logger as logger

# In service modules
from app.core.logger import service_logger as logger
```

This helps with filtering and organizing logs when analyzing them later.
