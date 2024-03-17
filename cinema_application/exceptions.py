"""
Custom HTTP exceptions
"""
from dataclasses import dataclass
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
)


@dataclass
class NotFoundException(HTTPException):
    status_code: int = HTTP_404_NOT_FOUND
    detail: str = "Not found"


@dataclass
class MovieOrRoomNotFoundException(HTTPException):
    status_code: int = HTTP_404_NOT_FOUND
    detail: str = "Room or Movie not found"


@dataclass
class MovieSessionNotFoundException(HTTPException):
    status_code: int = HTTP_404_NOT_FOUND
    detail: str = "Movie session not found"


@dataclass
class WrongParametersException(HTTPException):
    status_code: int = HTTP_400_BAD_REQUEST
    detail: str = "Minimum one parameter not found"


@dataclass
class AuthenticationFailed(HTTPException):
    status_code: int = HTTP_401_UNAUTHORIZED
    detail: str = "Authentication Failed"


@dataclass
class UserNotFoundException(HTTPException):
    status_code: int = HTTP_404_NOT_FOUND
    detail: str = "User not found"
