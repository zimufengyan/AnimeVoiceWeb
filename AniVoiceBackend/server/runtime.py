import json
import logging
import os
from pathlib import Path

import redis
from fastapi.security import OAuth2PasswordBearer
from fastapi_mail import ConnectionConfig, FastMail
from passlib.context import CryptContext

from database_fast import AudioRecordManager, DatabaseConfig, UserManager
from setting import Settings
from utils import configure_root_logger


settings = Settings()
db_config = DatabaseConfig(settings.SQLALCHEMY_DATABASE_URI)
user_manager = UserManager(db_config)
audio_record_manager = AudioRecordManager(db_config)
addr = f"http://{settings.APP_HOST}:{settings.APP_PORT}"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)

configure_root_logger(
    logging.DEBUG,
    file_path=os.path.join(settings.BASE_DIR, "backend_runtime.log"),
    max_size=10,
    backup_count=3,
)

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

character_info_path = os.path.join(settings.BASE_DIR, "character_info.json")
with open(character_info_path, "r", encoding="utf-8") as file:
    character_dic = json.loads(file.read())
    logging.info("successfully load character_info.json")

ip_characters_manifest_path = settings.IP_CHARACTERS_MANIFEST
with open(ip_characters_manifest_path, "r", encoding="utf-8") as file:
    ip_characters_manifest = json.loads(file.read())
    logging.info("successfully load ip_characters.json")

current_activated_character: str | None = None


def set_current_activated_character(character_name: str | None) -> None:
    global current_activated_character
    current_activated_character = character_name


def get_current_activated_character() -> str | None:
    return current_activated_character


def ensure_runtime_directories() -> None:
    Path(settings.UPLOAD_ICONS_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.PROFILE_BANNERS_DIR).mkdir(parents=True, exist_ok=True)
