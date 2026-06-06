from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from kairox_api.constants.enums import ErrorCode


class AppError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def error_response(
    code: ErrorCode,
    message: str,
    status_code: int = 400,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "error": {
            "code": code.value,
            "message": message,
        }
    }
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    err = exc if isinstance(exc, AppError) else AppError(ErrorCode.INTERNAL_ERROR, str(exc), 500)
    return error_response(err.code, err.message, err.status_code, err.details)
