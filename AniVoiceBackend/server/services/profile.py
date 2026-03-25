from fastapi import Request

from ..common import build_base_url, build_optional_asset_url
from ..runtime import settings
from ..schemas.profile import UserItem


def build_avatar_url(request: Request, avatar_filename: str | None) -> str:
    return build_optional_asset_url(build_base_url(request), avatar_filename, settings.UPLOAD_ICONS_LOCAL_DIR)


def build_banner_url(request: Request, banner_value: str | None) -> str:
    return build_optional_asset_url(
        build_base_url(request),
        banner_value,
        settings.PROFILE_BANNERS_LOCAL_DIR,
    )


def build_profile_payload(request: Request, current_user: UserItem, extra_fields: dict | None = None) -> dict:
    payload = {
        "username": current_user.name or "",
        "avatar": build_avatar_url(request, current_user.pic),
        "uid": current_user.uid,
        "rate": current_user.rate or "",
        "signature": current_user.signature or "",
        "profile_banner": build_banner_url(request, current_user.profile_banner),
        "birthday": current_user.birthday.isoformat() if current_user.birthday else "",
        "gender": current_user.gender or "",
    }
    if extra_fields:
        payload.update({key: value for key, value in extra_fields.items() if value is not None})
    return payload
