# 基于FastAPI的实现版本

import asyncio
import glob
import json
import logging
import os
import re
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import aiofiles
import httpx
import redis
from fastapi import Body, Depends, FastAPI, File, HTTPException, Query, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jose import JWTError, jwt
from passlib.context import CryptContext

from utils import *
from setting import Settings
from form_fast import *
from form import TTSReqForm
from database_fast import DatabaseConfig, UserManager, UserItem, AudioRecordItem, AudioRecordManager
from save_big_file import *


settings = Settings()
db_config = DatabaseConfig(settings.SQLALCHEMY_DATABASE_URI)
user_manager = UserManager(db_config)
audio_record_manager = AudioRecordManager(db_config)

addr = f'http://{settings.APP_HOST}:{settings.APP_PORT}'

app = FastAPI()
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")    # 挂载静态文件目录

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全相关
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Redis 客户端
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

# 日志配置
configure_root_logger(
    logging.DEBUG,
    file_path=os.path.join(settings.BASE_DIR, "backend_runtime.log"),
    max_size=10,
    backup_count=3,
)

# 邮件客户端配置
fast_mail = None
if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
    mail_conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_USERNAME,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_USE_TLS,
        MAIL_SSL_TLS=settings.MAIL_USE_SSL,
    )
    fast_mail = FastMail(mail_conf)
else:
    logging.warning("Mail service is disabled because MAIL_USERNAME or MAIL_PASSWORD is not configured.")


def build_base_url(request: Request) -> str:
    """构造当前请求对应的服务根地址。"""
    return str(request.base_url).rstrip("/")


def calculate_age_from_birthday(birthday: Optional[date]) -> Optional[int]:
    """
    根据生日计算当前年龄，生日为空时返回 None。
    :param birthday: 数据库中的生日日期。
    """
    if birthday is None:
        return None
    today = datetime.utcnow().date()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))


def build_static_asset_url(request: Request, local_dir: str, filename: str) -> str:
    """
    根据当前请求和静态资源相对目录生成完整可访问地址。
    :param request: 当前 FastAPI 请求对象。
    :param local_dir: 资源在静态目录下的相对 Web 路径。
    :param filename: 资源文件名。
    """
    return f"{build_base_url(request)}/{join_url_path(local_dir, filename)}"


def build_optional_asset_url(base_url: str, asset_value: Optional[str], local_dir: str) -> str:
    """
    将数据库中的资源字段转换成可访问 URL，兼容完整 URL、Data URL、本地静态路径和纯文件名。
    :param base_url: 当前服务根地址。
    :param asset_value: 数据库中的资源字段值。
    :param local_dir: 纯文件名场景下的静态目录。
    """
    if not asset_value:
        return ""
    if re.match(r"^(https?:)?//", asset_value) or asset_value.startswith("data:"):
        return asset_value
    if asset_value.startswith("/static/") or asset_value.startswith("static/"):
        return f"{base_url}/{asset_value.lstrip('/')}"
    return f"{base_url}/{join_url_path(local_dir, asset_value)}"


def join_url_path(*parts: str) -> str:
    """将若干 URL 路径片段拼接成标准 Web 路径。"""
    normalized = [part.strip("/\\") for part in parts if part]
    return "/".join(normalized)


def resolve_local_backend_path(path_str: str) -> str:
    """
    将配置中的后端路径映射到当前本地工作区。
    :param path_str: 配置文件中记录的绝对路径或远端路径。
    """
    normalized = path_str.replace("\\", "/")
    marker = "/AniVoiceBackend/"
    if marker in normalized:
        suffix = normalized.split(marker, 1)[1]
        return str(Path(settings.BASE_DIR) / Path(suffix.replace("/", os.sep)))
    return path_str


def database_error_response(message: str = "数据库连接失败，请检查 PostgreSQL 配置") -> JSONResponse:
    """生成统一的数据库异常响应。"""
    return JSONResponse(
        content={"code": "-500", "message": message},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def model_config_error_response(message: str) -> JSONResponse:
    """生成统一的角色模型配置异常响应。"""
    return JSONResponse(
        content={"code": "-3", "message": message},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def get_email_code_redis_key(email: str, prefix: str) -> str:
    """
    生成验证码在 Redis 中的存储键。
    :param email: 目标邮箱。
    :param prefix: 当前业务使用的键前缀。
    """
    return f"{prefix}{email.lower()}"


def load_email_code_from_redis(email: str, prefix: str) -> Optional[str]:
    """
    从 Redis 读取邮箱验证码。
    :param email: 目标邮箱。
    :param prefix: 当前业务使用的键前缀。
    """
    return redis_client.get(get_email_code_redis_key(email, prefix))


def consume_email_code(email: str, code: str, prefix: str) -> tuple[bool, str]:
    """
    校验并消费邮箱验证码，避免同一验证码重复使用。
    :param email: 目标邮箱。
    :param code: 用户提交的验证码。
    :param prefix: 当前业务使用的键前缀。
    """
    redis_key = get_email_code_redis_key(email, prefix)
    cached_code = redis_client.get(redis_key)
    if not cached_code:
        return False, "验证码不存在或已过期"
    if cached_code.strip() != code.strip():
        return False, "验证码错误"
    redis_client.delete(redis_key)
    return True, ""


async def send_verification_code_email(
    email: str,
    subject: str,
    body_builder,
    redis_prefix: str,
) -> JSONResponse | dict:
    """
    向指定邮箱发送业务验证码，并写入 Redis。
    :param email: 接收验证码的邮箱地址。
    :param subject: 邮件主题。
    :param body_builder: 负责生成邮件正文的回调。
    :param redis_prefix: 当前业务使用的 Redis 键前缀。
    """
    if fast_mail is None:
        return JSONResponse(
            content={"code": -1, "message": "邮件服务未配置，请先设置 MAIL_USERNAME 和 MAIL_PASSWORD"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if not validate_email(email):
        return JSONResponse(content={"code": "-1", "message": "邮箱格式错误"}, status_code=400)

    verification_code = ''.join(random.choices('0123456789', k=6))
    timeout = settings.CODE_TIMEOUT
    body = body_builder(verification_code, timeout)

    try:
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=body,
            subtype="plain"
        )
        await fast_mail.send_message(message)
        redis_client.setex(
            get_email_code_redis_key(email, redis_prefix),
            timeout,
            verification_code,
        )
        logging.info("verification code sent to %s for prefix %s", email, redis_prefix)
        return {"code": 1, "message": "验证码发送成功"}
    except Exception as exc:
        logging.error("邮件发送失败: %s", str(exc), exc_info=True)
        return JSONResponse(
            content={"code": -1, "message": f"发送邮件失败: {str(exc)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def build_avatar_url(request: Request, avatar_filename: Optional[str]) -> str:
    """
    根据当前请求和头像字段内容生成可访问的头像地址。
    :param request: 当前 FastAPI 请求对象。
    :param avatar_filename: 数据库中保存的头像文件名或已是完整 URL 的头像值。
    """
    return build_optional_asset_url(build_base_url(request), avatar_filename, settings.UPLOAD_ICONS_LOCAL_DIR)


def build_banner_url(request: Request, banner_value: Optional[str]) -> str:
    """
    根据当前请求和横幅字段内容生成可访问的横幅地址。
    :param request: 当前 FastAPI 请求对象。
    :param banner_value: 数据库中保存的横幅文件名或已是完整 URL 的横幅值。
    """
    return build_optional_asset_url(build_base_url(request), banner_value, settings.PROFILE_BANNERS_LOCAL_DIR)


def infer_asset_extension(upload: UploadFile) -> str:
    """
    为上传文件推断安全的扩展名，缺失时按内容类型补一个默认值。
    :param upload: FastAPI 接收到的上传文件对象。
    """
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
    """
    将上传文件保存到指定目录，并返回生成后的文件名。
    :param upload: FastAPI 接收到的上传文件对象。
    :param target_dir: 目标存储目录。
    """
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


def build_profile_payload(
    request: Request,
    current_user: UserItem,
    extra_fields: Optional[dict] = None,
) -> dict:
    """
    组装个人中心接口统一返回的用户资料结构。
    :param request: 当前 FastAPI 请求对象。
    :param current_user: 当前登录用户。
    :param extra_fields: 当前接口需要额外覆盖的资料字段。
    """
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


def profile_not_implemented_response(request: Request, current_user: UserItem, message: str) -> JSONResponse:
    """
    返回个人资料相关接口的占位响应，方便前后端先对齐契约。
    :param request: 当前 FastAPI 请求对象。
    :param current_user: 当前登录用户。
    :param message: 当前占位接口的说明信息。
    """
    return JSONResponse(
        content={
            "meta": {"code": "-1", "message": message},
            "profile": build_profile_payload(request, current_user),
        },
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )


# 读取角色-模型数据
character_info_path = os.path.join(settings.BASE_DIR, "character_info.json")
with open(character_info_path, 'r', encoding='utf-8') as f:
    character_dic = json.loads(f.read())
    logging.info("successfuy load character_info.json")

current_activated_character = None  # 当前激活的角色

CHARACTER_NAME_ALIASES = {
    "Kamizato Ayaka": "Ayaka",
    "Kamisato Ayaka": "Ayaka",
    "Yae Miko": "YaeMiko",
}


def canonicalize_character_name(name: str, belong: Optional[str] = None) -> str:
    """
    将前端展示名或素材文件名归一化为后端模型配置中的标准角色键名。
    :param name: 前端传入的角色名或素材文件名。
    :param belong: 角色所属 IP，用于在当前角色集合中做二次匹配。
    """
    raw_name = os.path.splitext(name)[0].strip()
    if not raw_name:
        return raw_name

    if raw_name in CHARACTER_NAME_ALIASES:
        return CHARACTER_NAME_ALIASES[raw_name]

    normalized_raw = raw_name.replace(" ", "").lower()
    if belong in character_dic:
        for character_name in character_dic[belong].keys():
            if character_name.replace(" ", "").lower() == normalized_raw:
                return character_name

    return raw_name


def resolve_character_asset_filename(directory: str, belong: str, character_name: str, ext: str) -> str:
    """
    按标准角色键名反查素材目录中的真实文件名。
    :param directory: 素材根目录。
    :param belong: 角色所属 IP。
    :param character_name: 标准化后的角色键名。
    :param ext: 文件扩展名。
    """
    character_dir = Path(directory) / belong
    exact_name = f"{character_name}.{ext}"
    if (character_dir / exact_name).exists():
        return exact_name

    for asset_path in sorted(character_dir.glob(f"*.{ext}")):
        if canonicalize_character_name(asset_path.stem, belong) == character_name:
            return asset_path.name

    return exact_name


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + settings.ACCESS_TOKEN_EXPIRES

    # 添加唯一标识 jti
    to_encode.update({
        "exp": expire,
        "jti": str(uuid.uuid4())  # 生成唯一标识符
    })
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


# ----------------------- 依赖项 -----------------------
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    解析登录令牌并按展示 UID 获取当前用户。
    :param token: Bearer 令牌字符串。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )

        # 检查 Token 是否在黑名单
        jti = payload.get("jti")
        if not jti or redis_client.exists(f"blacklist:{jti}"):
            raise credentials_exception

        uid_value = payload.get("sub")
        if uid_value is None:
            raise credentials_exception
        user = await user_manager.get_user_by_uid(int(uid_value))
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user


# ----------------------- 中间件 -----------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as exc:
        logging.error(f"Unhandled server error: {exc}", exc_info=True)
        response = JSONResponse(
            content={"code": "-500", "message": "服务器内部错误"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.on_event("startup")
async def startup_event():
    Path(settings.UPLOAD_ICONS_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.PROFILE_BANNERS_DIR).mkdir(parents=True, exist_ok=True)
    await db_config.init_models()


# ----------------------- 路由部分 -----------------------
@app.post("/login", response_model=LoginRegisterResponse)
async def login(form: LoginRequest = Body(...)):
    """
    处理用户登录，兼容前端已加密密码和明文密码两种输入方式。
    :param form: 登录表单，请求中 password 可能是明文，也可能是前端按 salt 预先加密后的值。
    """
    logging.info('post for login')
    
    user = await user_manager.get_user_by_email(form.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    password_matches = form.password == user.pwd
    if not password_matches:
        try:
            password_matches = pwd_context.verify(form.password, user.pwd)
        except Exception:
            password_matches = False

    if not password_matches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="incorrect password"
        )
    
    access_token = create_access_token(
        data={"sub": str(user.uid)},
        expires_delta=settings.ACCESS_TOKEN_EXPIRES
    )
    avatar_url = build_optional_asset_url(addr, user.pic, settings.UPLOAD_ICONS_LOCAL_DIR)
    
    return {
        "meta": MetaResponse(code="1", message="登陆成功"),
        "username": user.name,
        "avatar": avatar_url,
        "uid": user.uid,
        "rate": user.rate,
        "token": access_token,
    }


@app.post("/register", response_model=LoginRegisterResponse)
async def register(form: RegisterRequest = Body(...)):
    """
    处理用户注册，完成验证码校验、默认资料生成和用户落库。
    :param form: 前端提交的注册表单，密码为前端已加密后的 bcrypt 结果。
    """
    logging.info('post for register')

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
    

@app.get('/get_email_code')
async def get_email_code(email: str):
    logging.info(f'get email code for {email}')
    return await send_verification_code_email(
        email=email,
        subject="注册验证码",
        body_builder=lambda verification_code, timeout: (
            f"您好，您正在注册 AnimeVoice，验证码是：{verification_code}，"
            f"请在 {timeout // 60} 分钟内完成注册。"
        ),
        redis_prefix=settings.CODE_REDIS_KEY_PERFIX,
    )


@app.post("/forgot_password/send_code")
async def send_reset_password_code(form: EmailCodeRequest = Body(...)):
    """
    向已注册邮箱发送找回密码验证码。
    :param form: 仅包含邮箱地址的请求体。
    """
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


@app.post("/forgot_password/reset")
async def reset_password(form: ResetPasswordRequest = Body(...)):
    """
    校验重置验证码并更新用户密码哈希与 salt。
    :param form: 包含邮箱、验证码、前端加密密码和 salt 的请求体。
    """
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


@app.post("/logout")
async def logout(
    current_user: UserItem = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}  # 允许过期 Token 登出
        )
        
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if not jti or not exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )

        # 计算剩余有效时间（即使已过期也处理）
        expire_time = datetime.fromtimestamp(exp)
        remaining_time = expire_time - datetime.utcnow()
        
        # 将 jti 加入黑名单（保留至原过期时间）
        if remaining_time.total_seconds() > 0:
            await redis_client.setex(
                f"blacklist:{jti}",
                int(remaining_time.total_seconds()),
                "true"
            )

        return {"code": "1", "message": "登出成功"}
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@app.get("/get_salt")
async def get_salt(email: str):
    try:
        user = await user_manager.get_user_by_email(email)
    except Exception as exc:
        logging.error(f"Database error during get_salt: {exc}", exc_info=True)
        return database_error_response()

    if not user:
        return JSONResponse(
            content={"code": "3", "message": "该用户不存在, 请注册"},
            status_code=200
        )
    return {"code": 1, "message": "获取成功", "salt": user.salt}


@app.post('/generate_voice')
async def generate_voice(
    request: Request,
    current_user: UserItem = Depends(get_current_user),
    form: TTSRequest = Body(...)
):
    logging.info(f'current user: {current_user}')
    character_name = canonicalize_character_name(form.character, form.belong)
    if character_name != form.character:
        logging.info("normalized character name from %s to %s", form.character, character_name)
        form.character = character_name

    if form.belong not in character_dic:
        logging.warning(f"belong {form.belong} not in character_dic")
        return JSONResponse(
            content={"code": "-1", "message": "该IP不存在"},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    all_characters: dict = character_dic[form.belong]
    if form.character not in all_characters:
        logging.warning(f"character {form.character} not in all_characters")
        return JSONResponse(
            content={"code": "-2", "message": "该角色不存在或暂不支持"},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    
    model_info = all_characters[form.character]
    required_model_keys = [
        "gpt_weights_path",
        "sovits_weights_path",
        "promot_lang",
        "prompt_text_path",
        "ref_audio_path",
    ]
    missing_keys = [key for key in required_model_keys if not model_info.get(key)]
    if missing_keys:
        logging.warning(
            "character %s missing model config keys: %s",
            form.character,
            ", ".join(missing_keys),
        )
        return model_config_error_response(f"角色 {form.character} 缺少模型配置，暂时无法生成语音")

    global current_activated_character

    if not current_activated_character or form.character != current_activated_character:
        # 角色改变，重新设置模型
        # prepare SOVITS backend
        logging.info(f"set model for character: {form.character}")
        try:
            succ1, _ = await async_execute_request(
                url=settings.SOVITS_SET_GPT_API,
                param={'weights_path': model_info['gpt_weights_path']}
            )
            succ2, _ = await async_execute_request(
                url=settings.SOVITS_SET_VIT_API,
                param={'weights_path': model_info['sovits_weights_path']}
            )
        except Exception as exc:
            logging.error(f"failed to reach GPT-SoVITS weight APIs: {exc}", exc_info=True)
            return JSONResponse(
                content={"code": "-1", "message": f"无法连接 GPT-SoVITS 服务: {settings.SOVITS_ADDR}"},
                status_code=status.HTTP_502_BAD_GATEWAY,
            )

        if not succ1 or not succ2:
            return JSONResponse(
                content={"code": "-1", "message": f"GPT-SoVITS 模型切换失败: {settings.SOVITS_ADDR}"},
                status_code=status.HTTP_502_BAD_GATEWAY,
            )
        logging.info(f"successfully set model for character: {form.character}")
        current_activated_character = form.character

    prompt_text_path = resolve_local_backend_path(model_info['prompt_text_path'])
    if not os.path.exists(prompt_text_path):
        logging.error("prompt text file not found: %s", prompt_text_path)
        return JSONResponse(
            content={"code": "-4", "message": f"提示词文件不存在: {prompt_text_path}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    async with aiofiles.open(prompt_text_path, 'r', encoding='utf-8') as f:
        prompt_text = (await f.read()).replace('/n', '').strip()

    tts_data = TTSReqForm(
        text = form.text, text_lang=form.lang, ref_audio_path=model_info['ref_audio_path'],
        prompt_lang=model_info['promot_lang'], prompt_text=prompt_text
    )
    logging.info(
        "sending TTS request to %s with ref_audio_path=%s prompt_lang=%s",
        settings.SOVITS_TTS_API,
        tts_data.ref_audio_path,
        tts_data.prompt_lang,
    )
    # succ, response = await async_execute_request(settings.SOVITS_TTS_API, 
    #                                             param=form.to_dict())
    # if not succ:
    #     return JSONResponse(content={"code" : "-1", "messaage": "无法连接GPT-SoVITS"}, status_code=500)
    # logging.info('successfully generate voice')

    unique_id = str(uuid.uuid4())
    audio_dir = Path(settings.GENERATED_AUDIO_DIR)
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / (unique_id + '.wav')
    audio_local_path = join_url_path(settings.GENERATED_AUDIO_LOCAL_DIR, unique_id + '.wav')
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 发送异步请求到TTS服务
            response = await client.post(
                settings.SOVITS_TTS_API,
                json=tts_data.to_dict(),
                headers={"Content-Type": "application/json"}
            )
        except httpx.HTTPError as exc:
            logging.error(f"failed to reach GPT-SoVITS TTS API: {exc}", exc_info=True)
            return JSONResponse(
                content={"code": "-1", "message": f"无法连接 GPT-SoVITS 语音接口: {settings.SOVITS_TTS_API}"},
                status_code=status.HTTP_502_BAD_GATEWAY,
            )

        if response.status_code != 200:
            logging.error("GPT-SoVITS TTS API returned %s: %s", response.status_code, response.text)
            return JSONResponse(
                content={"code": "-1", "message": f"GPT-SoVITS 返回异常: {response.status_code}"},
                status_code=status.HTTP_502_BAD_GATEWAY,
            )

        # 流式模式处理
        if tts_data.streaming_mode:
            async def streaming_wrapper():
                async for chunk in response.aiter_bytes():
                    yield chunk
            
            # 创建异步保存任务
            save_task = asyncio.create_task(
                save_wav_stream(streaming_wrapper(), audio_path)
            )
            
            # # 返回流式响应
            # return StreamingResponse(
            #     streaming_wrapper(),
            #     media_type=response.headers.get("content-type", "audio/wav")
            # )
        
        # 非流式模式处理
        else:
            audio_data = response.content
            await save_wav_bytes(audio_data, audio_path)

        logging.info(f"successfully write audio into path : {audio_path}")     
        base_url = build_base_url(request)
        local_audio_url = f"{base_url}/{audio_local_path}"
        avatar_filename = resolve_character_asset_filename(
            settings.CHARACTER_AVATOR_DIR,
            form.belong,
            form.character,
            settings.CHARACTER_AVATOR_EXT,
        )
        character_avatar_url = f"{base_url}/{join_url_path(settings.CHARACTER_AVATOR_LOCAL_DIR, form.belong, avatar_filename)}"

        record_created, record_message = await audio_record_manager.create_audio_record(
            AudioRecordItem(
                user_id=current_user.id,
                audio_character=form.character,
                audio_belong=form.belong,
                audio_path=local_audio_url,
                audio_text=form.text,
                text_lang=form.lang,
                character_avator_path=character_avatar_url,
                audio_filename=audio_path.name,
            )
        )
        if not record_created:
            logging.warning("failed to create audio record: %s", record_message)

        return {"code": 1, "audio_url": local_audio_url, "message": "语音生成成功"}
            

@app.get("/get_recent_audio_records", response_model=AudioRecordResponse)
async def get_recent_audio_records(current_user: dict = Depends(get_current_user)):
    logging.info(f'current user: {current_user.name}')
    succ, records = await audio_record_manager.get_rencent_audio_records_by_user_id(current_user.id, days=settings.AUDIO_RECORD_EXPIRE)
    if not succ:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="faild to get recent audio records")

    return {"meta": MetaResponse(code="1", message="获取成功"), "records": records}


@app.get("/delete_audio_record")
async def delete_audio_record(current_user: dict = Depends(get_current_user), audio_id: int = Query(...)):
    logging.info(f'current user: {current_user.name}')
    succ, message = await audio_record_manager.delete_audio_record_by_id(audio_id)
    logging.info(message)
    if not succ:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    
    # 重新返回最新记录
    succ, records = await audio_record_manager.get_rencent_audio_records_by_user_id(current_user.id, days=settings.AUDIO_RECORD_EXPIRE)
    if not succ:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="faild to get recent audio records")

    return {"meta": MetaResponse(code="1", message="删除成功"), "records": records}


@app.get("/profile", response_model=UserProfileResponse)
async def get_profile(request: Request, current_user: UserItem = Depends(get_current_user)):
    """获取当前登录用户的个人资料，未持久化字段先返回空字符串供前端本地兜底。"""
    return {
        "meta": MetaResponse(code="1", message="获取成功"),
        "profile": build_profile_payload(request, current_user),
    }


@app.put("/profile")
async def update_profile(
    request: Request,
    form: UpdateProfileRequest = Body(...),
    current_user: UserItem = Depends(get_current_user),
):
    """
    更新当前登录用户的核心资料字段，并将未持久化字段原样回传给前端做本地兜底。
    :param request: 当前 FastAPI 请求对象。
    :param form: 前端提交的资料更新负载。
    :param current_user: 当前登录用户。
    """
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="个人资料更新失败",
            )
        current_user = await user_manager.get_user_by_id(current_user.id)
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )

    return {
        "meta": MetaResponse(code="1", message="更新成功"),
        "profile": build_profile_payload(
            request,
            current_user,
        ),
    }


@app.post("/profile/avatar", response_model=ProfileUploadResponse)
async def upload_profile_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserItem = Depends(get_current_user),
):
    """
    上传用户头像文件，保存后同步更新数据库中的头像字段。
    :param request: 当前 FastAPI 请求对象。
    :param file: 前端上传的头像图片文件。
    :param current_user: 当前登录用户。
    """
    logging.info("upload avatar for user %s: %s", current_user.id, file.filename)
    avatar_filename = await save_uploaded_asset(file, settings.UPLOAD_ICONS_DIR)
    updated = await user_manager.update_user(current_user.id, {"pic": avatar_filename})
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="头像保存成功，但用户资料更新失败",
        )

    refreshed_user = await user_manager.get_user_by_id(current_user.id)
    if refreshed_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    asset_url = build_static_asset_url(request, settings.UPLOAD_ICONS_LOCAL_DIR, avatar_filename)
    return {
        "meta": MetaResponse(code="1", message="头像上传成功"),
        "profile": build_profile_payload(request, refreshed_user),
        "asset_url": asset_url,
    }


@app.post("/profile/banner", response_model=ProfileUploadResponse)
async def upload_profile_banner(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserItem = Depends(get_current_user),
):
    """
    上传用户横幅图片，当前先返回资源地址，由前端负责本地持久化该字段。
    :param request: 当前 FastAPI 请求对象。
    :param file: 前端上传的横幅图片文件。
    :param current_user: 当前登录用户。
    """
    logging.info("upload banner for user %s: %s", current_user.id, file.filename)
    banner_filename = await save_uploaded_asset(file, settings.PROFILE_BANNERS_DIR)
    updated = await user_manager.update_user(current_user.id, {"profile_banner": banner_filename})
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="横幅保存成功，但用户资料更新失败",
        )

    refreshed_user = await user_manager.get_user_by_id(current_user.id)
    if refreshed_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    asset_url = build_static_asset_url(request, settings.PROFILE_BANNERS_LOCAL_DIR, banner_filename)
    return {
        "meta": MetaResponse(code="1", message="横幅上传成功"),
        "profile": build_profile_payload(request, refreshed_user),
        "asset_url": asset_url,
    }


@app.get('/delete_audio_records')
async def delete_audio_records(current_user: dict = Depends(get_current_user), audio_ids: List[int] = Query(...)):
    logging.info(f'current user: {current_user.name}')
    succ, message = await audio_record_manager.delete_audio_records_by_ids(audio_ids)
    logging.info(message)
    if not succ:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    
    # 重新返回最新记录
    succ, records = await audio_record_manager.get_rencent_audio_records_by_user_id(current_user.id, days=settings.AUDIO_RECORD_EXPIRE)
    if not succ:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="faild to get recent audio records")

    return {"meta": MetaResponse(code="1", message="删除成功"), "records": records}


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = Path(f"uploads/{filename}")
    
    if not file_path.is_file():
        return {"error": "File not found"}
    
    # 异步读取并流式传输
    async def file_sender():
        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(1024 * 1024):  # 1MB 分块
                yield chunk
    
    return StreamingResponse(file_sender(), media_type="application/octet-stream")


@app.get("/get_belong_statics")
async def get_belong_statics(request: Request, belong: Optional[str] = Query(None)):
    logging.info(f"get belong statics for {belong}")
    if belong not in character_dic:
        # 不支持的IP
        logging.warning(f"belong {belong} not in character_dic")
        return JSONResponse(content={"code" : "-1", "messaage": "该IP不存在"}, status_code=201)
    
    avators = glob.glob(os.path.join(settings.CHARACTER_AVATOR_DIR, belong, f"*.{settings.CHARACTER_AVATOR_EXT}"))
    stands = glob.glob(os.path.join(settings.STANDS_DIR, belong, f"*.{settings.STAND_EXT}"))

    stands.sort()
    avators.sort()

    logging.info(f"capture {len(stands)} stands and {len(avators)} avators")
    if len(stands) != len(avators):
        logging.info(f"length of stands ({len(stands)}) != length of avators ({len(avators)})")
        return JSONResponse(content={"code" : "-2", "messaage": "角色数量不匹配"}, status_code=500)

    base_url = build_base_url(request)
    names, stand_urls, avator_urls = [], [], []
    for stand, avator in zip(stands, avators):
        names.append(canonicalize_character_name(os.path.splitext(os.path.basename(stand))[0], belong))
        stand_urls.append(f"{base_url}/{join_url_path(settings.STANDS_LOCAL_DIR, belong, os.path.basename(stand))}")
        avator_urls.append(f"{base_url}/{join_url_path(settings.CHARACTER_AVATOR_LOCAL_DIR, belong, os.path.basename(avator))}")

    return {"code": 1, "names": names, "stands": stand_urls, "avators": avator_urls}


# -------------------------- 启动部分 -----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_fast:app", host="0.0.0.0", port=settings.APP_PORT, reload=False)
