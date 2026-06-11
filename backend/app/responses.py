import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class APIError(Exception):
    """业务异常，携带错误码与详情。"""

    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def new_request_id() -> str:
    return str(uuid.uuid4())


def ok(data: Any, warnings: list[str] | None = None) -> dict:
    return {"data": data, "meta": {"request_id": new_request_id(), "warnings": warnings or []}}


def ok_list(data: list, page: int, page_size: int, total: int, warnings: list[str] | None = None) -> dict:
    return {
        "data": data,
        "pagination": {"page": page, "page_size": page_size, "total": total},
        "meta": {"request_id": new_request_id(), "warnings": warnings or []},
    }


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"code": exc.code, "message": exc.message, "details": exc.details},
            "meta": {"request_id": new_request_id()},
        },
    )
