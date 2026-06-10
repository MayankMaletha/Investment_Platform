"""core/exceptions.py — Domain exceptions and FastAPI handlers."""

from typing import Any
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from core.logging import logger


class AppException(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Any = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: Any = None):
        super().__init__(status.HTTP_404_NOT_FOUND, "NOT_FOUND", f"{resource} not found",
                         {"identifier": str(identifier)} if identifier else None)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", message)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(status.HTTP_403_FORBIDDEN, "FORBIDDEN", message)


class ValidationError(AppException):
    def __init__(self, message: str, details: Any = None):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", message, details)


class ExternalServiceError(AppException):
    def __init__(self, service: str, message: str):
        super().__init__(status.HTTP_502_BAD_GATEWAY, "EXTERNAL_SERVICE_ERROR",
                         f"External service '{service}' error: {message}")


class RateLimitError(AppException):
    def __init__(self):
        super().__init__(status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMIT_EXCEEDED",
                         "Too many requests. Please try again later.")


class InsufficientFundsError(AppException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, "INSUFFICIENT_FUNDS",
                         "Insufficient funds for this transaction.")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("Application exception", code=exc.code, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "details": errors}},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception", path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."}},
    )
