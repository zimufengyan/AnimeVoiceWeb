import os
import re
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse


def build_base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def calculate_age_from_birthday(birthday: Optional[date]) -> Optional[int]:
    if birthday is None:
        return None
    today = datetime.utcnow().date()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))


def join_url_path(*parts: str) -> str:
    normalized = [part.strip("/\\") for part in parts if part]
    return "/".join(normalized)


def build_static_asset_url(request: Request, local_dir: str, filename: str) -> str:
    return f"{build_base_url(request)}/{join_url_path(local_dir, filename)}"


def build_optional_asset_url(base_url: str, asset_value: Optional[str], local_dir: str) -> str:
    if not asset_value:
        return ""
    if re.match(r"^(https?:)?//", asset_value) or asset_value.startswith("data:"):
        return asset_value
    if asset_value.startswith("/static/") or asset_value.startswith("static/"):
        return f"{base_url}/{asset_value.lstrip('/')}"
    return f"{base_url}/{join_url_path(local_dir, asset_value)}"


def resolve_local_backend_path(path_str: str) -> str:
    from .runtime import settings

    normalized = path_str.replace("\\", "/")
    marker = "/AniVoiceBackend/"
    if marker in normalized:
        suffix = normalized.split(marker, 1)[1]
        return str(Path(settings.BASE_DIR) / Path(suffix.replace("/", os.sep)))
    return path_str


def database_error_response(message: str = "数据库连接失败，请检查 PostgreSQL 配置") -> JSONResponse:
    return JSONResponse(
        content={"code": "-500", "message": message},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def model_config_error_response(message: str) -> JSONResponse:
    return JSONResponse(
        content={"code": "-3", "message": message},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def infer_asset_extension(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix:
        return suffix
    content_type = (upload.content_type or "").lower()
    if content_type == "image/jpeg":
        return ".jpg"
    if content_type == "image/gif":
        return ".gif"
    if content_type == "image/webp":
        return ".webp"
    return ".png"


async def save_uploaded_asset(upload: UploadFile, target_dir: str) -> str:
    if not (upload.content_type or "").lower().startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持上传图片文件",
        )

    Path(target_dir).mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}{infer_asset_extension(upload)}"
    file_path = Path(target_dir) / filename
    try:
        file_bytes = await upload.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="上传文件内容为空",
            )

        async with aiofiles.open(file_path, "wb") as asset_file:
            await asset_file.write(file_bytes)
    finally:
        await upload.close()

    return filename
