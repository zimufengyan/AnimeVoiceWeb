import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse


async def add_security_headers(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as exc:
        logging.error("Unhandled server error: %s", exc, exc_info=True)
        response = JSONResponse(
            content={"code": "-500", "message": "服务器内部错误"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
