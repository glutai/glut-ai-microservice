from fastapi import HTTPException, status
from typing import Any

class DatabaseError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Item not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class ValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class DatabaseError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(self.detail)

class ValidationError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(self.detail)