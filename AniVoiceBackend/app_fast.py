# 基于FastAPI的实现版本

import glob
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import aiofiles
import httpx
import redis
from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, status
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
from database_fast import DatabaseConfig, UserManager, UserItem
from save_big_file import *


settings = Settings()
db_config = DatabaseConfig(settings.SQLALCHEMY_DATABASE_URI)
user_manager = UserManager(db_config)

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
configure_root_logger(logging.DEBUG)

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
    return str(request.base_url).rstrip("/")


def join_url_path(*parts: str) -> str:
    normalized = [part.strip("/\\") for part in parts if part]
    return "/".join(normalized)


def database_error_response(message: str = "数据库连接失败，请检查 PostgreSQL 配置") -> JSONResponse:
    return JSONResponse(
        content={"code": "-500", "message": message},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


# 读取角色-模型数据
character_info_path = os.path.join(settings.BASE_DIR, "character_info.json")
with open(character_info_path, 'r', encoding='utf-8') as f:
    character_dic = json.loads(f.read())
    logging.info("successfuy load character_info.json")

current_activated_character = None  # 当前激活的角色


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
        
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
        user = await user_manager.get_user_by_id(int(user_id))
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


# ----------------------- 路由部分 -----------------------
@app.post("/login", response_model=LoginResponse)
async def login(request: Request, form: LoginRequest = Body(...)):
    logging.info('post for login')

    try:
        user = await user_manager.get_user_by_email(form.email)
    except Exception as exc:
        logging.error(f"Database error during login: {exc}", exc_info=True)
        return database_error_response()
    
    if not user:
        return JSONResponse(
            content={"code": "3", "message": "该用户不存在, 请注册"},
            status_code=200
        )
    
    if not pwd_context.verify(form.password, user.pwd):
        return JSONResponse(
            content={"code": "2", "message": "密码错误"},
            status_code=200
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=settings.ACCESS_TOKEN_EXPIRES
    )
    
    avatar_path = os.path.join(
        settings.UPLOAD_ICONS_LOCAL_DIR, 
        user.pic
    )
    base_url = build_base_url(request)
    avatar_url = f"{base_url}/{avatar_path.replace(os.sep, '/')}"
    
    return {
        "code": "1",
        "username": user.name,
        "avatar": avatar_url,
        "index": user.index,
        "rate": user.rate,
        "token": access_token,
        "message": "登陆成功"
    }


@app.get('/get_email_code')
async def get_email_code(email: str):
    logging.info(f'get email code for {email}')
    if fast_mail is None:
        return JSONResponse(
            content={"code": -1, "message": "邮件服务未配置，请先设置 MAIL_USERNAME 和 MAIL_PASSWORD"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    # 验证邮箱格式
    if not validate_email(email):
        return JSONResponse(content={"code" : "-1", "messaage": "邮箱格式错误"}, status_code=201)
    
    # 随机生成6位验证码
    verification_code = ''.join(random.choices('0123456789', k=6))
    timeout = settings.CODE_TIMEOUT

    # 构造邮件内容
    subject = "验证码"
    body = f"您好, 您正在注册本网站，您的验证码是：{verification_code}，请在 {timeout // 60} 分钟内使用。"

    try:
        # 发送邮件（异步）
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=body,
            subtype="plain"
        )
        await fast_mail.send_message(message)
        logging.info(f"验证码已发送至 {email}")
        
        # 存储至 Redis
        redis_key = f"{settings.CODE_REDIS_KEY_PERFIX}{email}"
        redis_client.setex(redis_key, timeout, verification_code)
        
        return {"code": 1, "message": "验证码发送成功"}
    
    except Exception as e:
        logging.error(f"邮件发送失败: {str(e)}", exc_info=True)
        return JSONResponse(
            content={"code": -1, "message": f"发送邮件失败: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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


@app.get('/generate_voice')
async def generate_voice(
    request: Request,
    current_user: UserItem = Depends(get_current_user),
    form: TTSRequest = Body(...)
):
    logging.info(f'current user: {current_user}')

    if form.belong not in character_dic:
        logging.warning(f"belong {form.belong} not in character_dic")
        return JSONResponse(content={"code" : "-1", "messaage": "该IP不存在"}, status_code=201)
    all_characters: dict = character_dic[form.belong]
    if form.character not in all_characters:
        logging.warning(f"character {form.character} not in all_characters")
        return JSONResponse(content={"code" : "-2", "messaage": "该角色不存在或暂不支持"}, status_code=201)
    
    model_info = all_characters[form.character]
    global current_activated_character

    if not current_activated_character or form.character != current_activated_character:
        # 角色改变，重新设置模型
        # prepare SOVITS backend
        logging.info(f"set model for character: {form.character}")
        succ1, _ = await async_execute_request(url=settings.SOVITS_SET_GPT_API, 
                        param={'weights_path': model_info['gpt_weights_path']})
        succ2, _ = await async_execute_request(url=settings.SOVITS_SET_VIT_API, 
                        param={'weights_path': model_info['sovits_weights_path']})
        if not succ1 or not succ2:
            return JSONResponse(content={"code" : "-1", "messaage": "无法连接GPT-SoVITS"}, status_code=500)
        logging.info(f"successfully set model for character: {form.character}")
        current_activated_character = form.character

    async with aiofiles.open(model_info['prompt_text_path'], 'r', encoding='utf-8') as f:
        prompt_text = await f.read().replace('/n', '').strip()

    tts_data = TTSReqForm(
        text = form.text, text_lang=form.lang, ref_audio_path=model_info['ref_audio_path'],
        prompt_lang=model_info['promot_lang'], prompt_text=prompt_text
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
        # 发送异步请求到TTS服务
        response = await client.post(
            settings.SOVITS_TTS_API,
            json=tts_data.to_dict(),
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

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
            # 后台保存任务
            asyncio.create_task(save_wav_bytes(audio_data, audio_path))

        logging.info(f"successfully write audio into path : {audio_path}")     
        base_url = build_base_url(request)
        local_audio_url = f"{base_url}/{audio_local_path}"
        return {"code": 1, "audio_url": local_audio_url, "message": "语音生成成功"}
            

@app.get("/get_recent_audio_records")
async def get_recent_audio_records(current_user: dict = Depends(get_current_user)):
    logging.info(f'current user: {current_user}')
    return {"code": 1, "message": "获取成功"}


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
        names.append(os.path.splitext(os.path.basename(stand))[0])
        stand_urls.append(f"{base_url}/{join_url_path(settings.STANDS_LOCAL_DIR, belong, os.path.basename(stand))}")
        avator_urls.append(f"{base_url}/{join_url_path(settings.CHARACTER_AVATOR_LOCAL_DIR, belong, os.path.basename(avator))}")

    return {"code": 1, "names": names, "stands": stand_urls, "avators": avator_urls}


# -------------------------- 启动部分 -----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_fast:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
