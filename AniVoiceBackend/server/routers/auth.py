import logging
import os
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError

from utils import generate_rate, get_random_image

from ..common import build_optional_asset_url, database_error_response
from ..runtime import addr, oauth2_scheme, pwd_context, redis_client, settings, user_manager
from ..schemas import EmailCodeRequest, LoginRegisterResponse, LoginRequest, MetaResponse, RegisterRequest, ResetPasswordRequest, UserItem
from ..security import create_access_token, decode_token, get_current_user
from ..services.email_codes import consume_email_code, send_verification_code_email


router = APIRouter()


@router.post("/login", response_model=LoginRegisterResponse)
async def login(form: LoginRequest = Body(...)):
    logging.info("post for login")
    user = await user_manager.get_user_by_email(form.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    password_matches = form.password == user.pwd
    if not password_matches:
        try:
            password_matches = pwd_context.verify(form.password, user.pwd)
        except Exception:
            password_matches = False

    if not password_matches:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="incorrect password")

    access_token = create_access_token(data={"sub": str(user.uid)}, expires_delta=settings.ACCESS_TOKEN_EXPIRES)
    avatar_url = build_optional_asset_url(addr, user.pic, settings.UPLOAD_ICONS_LOCAL_DIR)
    return {
        "meta": MetaResponse(code="1", message="登陆成功"),
        "username": user.name,
        "avatar": avatar_url,
        "uid": user.uid,
        "rate": user.rate,
        "token": access_token,
    }


@router.post("/register", response_model=LoginRegisterResponse)
async def register(form: RegisterRequest = Body(...)):
    logging.info("post for register")
    existing_user = await user_manager.get_user_by_email(form.email)
    if existing_user:
        return JSONResponse(
            content={"meta": {"code": "2", "message": "该邮箱已注册"}},
            status_code=status.HTTP_409_CONFLICT,
        )

    code_ok, code_message = consume_email_code(
        form.email,
        form.validation_code,
        settings.CODE_REDIS_KEY_PERFIX,
    )
    if not code_ok:
        return JSONResponse(
            content={"meta": {"code": "3", "message": code_message}},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    rate = generate_rate()
    avatar_path = get_random_image(settings.DEFAULT_ICON_DIR)
    avatar_name = os.path.basename(avatar_path) if avatar_path else ""

    user_item = UserItem(
        name=form.username.strip(),
        sex=0,
        pic=avatar_name,
        pwd=form.password,
        phone="",
        email=form.email.lower(),
        rate=rate,
        salt=form.salt,
        signature="",
        profile_banner="",
        gender="",
        birthday=None,
        age=None,
    )

    user_id, success = await user_manager.insert_user(user_item)
    if not success or user_id is None:
        return JSONResponse(
            content={"meta": {"code": "-1", "message": "注册失败，请稍后重试"}},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    created_user = await user_manager.get_user_by_id(user_id)
    if created_user is None:
        return JSONResponse(
            content={"meta": {"code": "-1", "message": "注册成功但用户资料读取失败"}},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    avatar_url = build_optional_asset_url(addr, created_user.pic, settings.UPLOAD_ICONS_LOCAL_DIR)
    return {
        "meta": MetaResponse(code="1", message="注册成功"),
        "username": created_user.name,
        "avatar": avatar_url,
        "uid": created_user.uid,
        "rate": created_user.rate,
    }


@router.get("/get_email_code")
async def get_email_code(email: str):
    logging.info("get email code for %s", email)
    return await send_verification_code_email(
        email=email,
        subject="注册验证码",
        body_builder=lambda verification_code, timeout: (
            f"您好，您正在注册 AnimeVoice，验证码是：{verification_code}，"
            f"请在 {timeout // 60} 分钟内完成注册。"
        ),
        redis_prefix=settings.CODE_REDIS_KEY_PERFIX,
    )


@router.post("/forgot_password/send_code")
async def send_reset_password_code(form: EmailCodeRequest = Body(...)):
    logging.info("send reset password code for %s", form.email)
    user = await user_manager.get_user_by_email(form.email)
    if not user:
        return JSONResponse(
            content={"code": "3", "message": "该用户不存在, 请注册"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return await send_verification_code_email(
        email=form.email,
        subject="密码重置验证码",
        body_builder=lambda verification_code, timeout: (
            f"您好，您正在重置 AnimeVoice 账号密码，验证码是：{verification_code}，"
            f"请在 {timeout // 60} 分钟内完成操作。如非本人操作，请忽略本邮件。"
        ),
        redis_prefix=settings.RESET_CODE_REDIS_KEY_PREFIX,
    )


@router.post("/forgot_password/reset")
async def reset_password(form: ResetPasswordRequest = Body(...)):
    logging.info("reset password for %s", form.email)
    user = await user_manager.get_user_by_email(form.email)
    if not user:
        return JSONResponse(
            content={"code": "3", "message": "该用户不存在, 请注册"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    code_ok, code_message = consume_email_code(
        form.email,
        form.validation_code,
        settings.RESET_CODE_REDIS_KEY_PREFIX,
    )
    if not code_ok:
        return JSONResponse(
            content={"code": "4", "message": code_message},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    updated = await user_manager.update_user(
        user.id,
        {
            "pwd": form.password,
            "salt": form.salt,
            "update_time": datetime.utcnow(),
        },
    )
    if not updated:
        return JSONResponse(
            content={"code": "-1", "message": "密码重置失败，请稍后重试"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return {"code": "1", "message": "密码重置成功"}


@router.post("/logout")
async def logout(current_user: UserItem = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token, verify_exp=False)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

        expire_time = datetime.fromtimestamp(exp)
        remaining_time = expire_time - datetime.utcnow()
        if remaining_time.total_seconds() > 0:
            redis_client.setex(f"blacklist:{jti}", int(remaining_time.total_seconds()), "true")
        return {"code": "1", "message": "登出成功"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.get("/get_salt")
async def get_salt(email: str):
    try:
        user = await user_manager.get_user_by_email(email)
    except Exception as exc:
        logging.error("Database error during get_salt: %s", exc, exc_info=True)
        return database_error_response()

    if not user:
        return JSONResponse(
            content={"code": "3", "message": "该用户不存在, 请注册", "salt": ""},
            status_code=200,
        )
    return {"code": 1, "message": "获取成功", "salt": user.salt}
