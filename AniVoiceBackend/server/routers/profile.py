import logging
from datetime import datetime

from fastapi import APIRouter, Body, Depends, File, HTTPException, Request, status, UploadFile

from ..common import build_static_asset_url, calculate_age_from_birthday, save_uploaded_asset
from ..runtime import settings, user_manager
from ..schemas import MetaResponse, ProfileUploadResponse, UpdateProfileRequest, UserItem, UserProfileResponse
from ..security import get_current_user
from ..services.profile import build_profile_payload


router = APIRouter()


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(request: Request, current_user: UserItem = Depends(get_current_user)):
    return {
        "meta": MetaResponse(code="1", message="获取成功"),
        "profile": build_profile_payload(request, current_user),
    }


@router.put("/profile")
async def update_profile(
    request: Request,
    form: UpdateProfileRequest = Body(...),
    current_user: UserItem = Depends(get_current_user),
):
    logging.info("update profile payload for user %s: %s", current_user.id, form.model_dump())
    updates = {}
    normalized_username = (form.username or "").strip()
    normalized_avatar = (form.avatar or "").strip()
    normalized_signature = (form.signature or "").strip()
    normalized_banner = (form.profile_banner or "").strip()
    birthday_value = datetime.strptime(form.birthday, "%Y-%m-%d").date() if form.birthday else None

    if normalized_username:
        updates["name"] = normalized_username
    updates["pic"] = normalized_avatar
    updates["signature"] = normalized_signature
    updates["profile_banner"] = normalized_banner
    updates["birthday"] = birthday_value
    updates["age"] = calculate_age_from_birthday(birthday_value)
    updates["gender"] = form.gender or ""

    if updates:
        updated = await user_manager.update_user(current_user.id, updates)
        if not updated:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="个人资料更新失败")

        current_user = await user_manager.get_user_by_id(current_user.id)
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return {
        "meta": MetaResponse(code="1", message="更新成功"),
        "profile": build_profile_payload(request, current_user),
    }


@router.post("/profile/avatar", response_model=ProfileUploadResponse)
async def upload_profile_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserItem = Depends(get_current_user),
):
    logging.info("upload avatar for user %s: %s", current_user.id, file.filename)
    avatar_filename = await save_uploaded_asset(file, settings.UPLOAD_ICONS_DIR)
    updated = await user_manager.update_user(current_user.id, {"pic": avatar_filename})
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="头像保存成功，但用户资料更新失败")

    refreshed_user = await user_manager.get_user_by_id(current_user.id)
    if refreshed_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    asset_url = build_static_asset_url(request, settings.UPLOAD_ICONS_LOCAL_DIR, avatar_filename)
    return {
        "meta": MetaResponse(code="1", message="头像上传成功"),
        "profile": build_profile_payload(request, refreshed_user),
        "asset_url": asset_url,
    }


@router.post("/profile/banner", response_model=ProfileUploadResponse)
async def upload_profile_banner(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserItem = Depends(get_current_user),
):
    logging.info("upload banner for user %s: %s", current_user.id, file.filename)
    banner_filename = await save_uploaded_asset(file, settings.PROFILE_BANNERS_DIR)
    updated = await user_manager.update_user(current_user.id, {"profile_banner": banner_filename})
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="横幅保存成功，但用户资料更新失败")

    refreshed_user = await user_manager.get_user_by_id(current_user.id)
    if refreshed_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    asset_url = build_static_asset_url(request, settings.PROFILE_BANNERS_LOCAL_DIR, banner_filename)
    return {
        "meta": MetaResponse(code="1", message="横幅上传成功"),
        "profile": build_profile_payload(request, refreshed_user),
        "asset_url": asset_url,
    }
