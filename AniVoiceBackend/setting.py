import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent


def _build_postgres_uri(
    driver: str,
    user: str,
    password: str,
    host: str,
    port: str | int,
    database: str,
) -> str:
    encoded_password = quote_plus(password or "")
    return f"{driver}://{user}:{encoded_password}@{host}:{port}/{database}"


class Config:
    # # 远程 Ollama 服务地址
    # HOST: str = os.getenv("OLLAMA_HOST", "10.60.102.53")
    # PORT: int = int(os.getenv("OLLAMA_PORT", "25683"))

    # 当前后端服务地址
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "98898"))

    # Postgres 数据库配置
    DATABASE_NAME: str = os.getenv("POSTGRES_DB", "postgres")
    USERTABLE_NAME: str = os.getenv("POSTGRES_USER_TABLE", "userinfo")
    DATABASE_USER: str = os.getenv("POSTGRES_USER", "postgres")
    DATABASE_PD: str = os.getenv("POSTGRES_PASSWORD", "")
    DATABASE_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI: str = _build_postgres_uri(
        "postgresql",
        DATABASE_USER,
        DATABASE_PD,
        DATABASE_HOST,
        DATABASE_PORT,
        DATABASE_NAME,
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Redis 配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "2"))

    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(days=1)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    # 项目路径
    BASE_DIR: str = str(BACKEND_DIR)
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")
    DEFAULT_ICON_DIR: str = os.path.join(STATIC_DIR, "default_icon")
    UPLOAD_ICONS_DIR: str = os.path.join(STATIC_DIR, "upload", "icon")
    UPLOAD_ICONS_LOCAL_DIR: str = "static/upload/icon/"
    STANDS_DIR: str = os.path.join(STATIC_DIR, "stands")
    STANDS_LOCAL_DIR: str = "static/stands/"
    STAND_EXT: str = "png"
    CHARACTER_AVATOR_DIR: str = os.path.join(STATIC_DIR, "character_avator")
    CHARACTER_AVATOR_LOCAL_DIR: str = "/static/character_avator"
    CHARACTER_AVATOR_EXT: str = "png"
    GENERATED_AUDIO_DIR: str = os.path.join(STATIC_DIR, "gen_audios")
    GENERATED_AUDIO_LOCAL_DIR: str = "/static/gen_audios"

    # 密码加密
    SALT_LENGTH: int = 12

    # 邮箱配置
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.163.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "465"))
    MAIL_USE_SSL: bool = os.getenv("MAIL_USE_SSL", "true").lower() == "true"
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    CODE_TIMEOUT: int = int(os.getenv("CODE_TIMEOUT", "300"))
    CODE_REDIS_KEY_PERFIX: str = os.getenv("CODE_REDIS_KEY_PREFIX", "email_code:")

    # GPT-SoVITS 配置
    SOVITS_ADDR: str = os.getenv("SOVITS_ADDR", "http://127.0.0.1:9880")
    SOVITS_SET_GPT_API: str = SOVITS_ADDR + "/set_gpt_weights"
    SOVITS_SET_VIT_API: str = SOVITS_ADDR + "/set_sovits_weights"
    SOVITS_TTS_API: str = SOVITS_ADDR + "/tts"


class DevelopmentConfig(Config):
    ENV: str = "development"
    DEBUG: bool = True


class ProductionConfig(Config):
    ENV = "production"
    DDEBUG = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env", PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 远程 Ollama 服务地址
    HOST: str = Field(default="10.60.102.53", validation_alias="OLLAMA_HOST")
    PORT: int = Field(default=25683, validation_alias="OLLAMA_PORT", ge=0, le=65535)

    # 当前后端服务地址
    APP_HOST: str = Field(default="127.0.0.1", validation_alias="APP_HOST")
    APP_PORT: int = Field(default=25683, validation_alias="APP_PORT", ge=0, le=65535)

    # Postgres 数据库配置
    DATABASE_NAME: str = Field(default="postgres", validation_alias="POSTGRES_DB")
    USERTABLE_NAME: str = Field(default="userinfo", validation_alias="POSTGRES_USER_TABLE")
    DATABASE_USER: str = Field(default="postgres", validation_alias="POSTGRES_USER")
    DATABASE_PD: str = Field(default="", validation_alias="POSTGRES_PASSWORD")
    DATABASE_HOST: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    DATABASE_PORT: int = Field(default=5432, validation_alias="POSTGRES_PORT", ge=0, le=65535)
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Redis 配置
    REDIS_HOST: str = Field(default="localhost", validation_alias="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, validation_alias="REDIS_PORT", ge=0, le=65535)
    REDIS_DB: int = Field(default=2, validation_alias="REDIS_DB")

    ACCESS_TOKEN_EXPIRES: timedelta = timedelta(days=1)
    SECRET_KEY: str = Field(default="change-me", validation_alias="APP_SECRET_KEY")
    ALGORITHM: str = "HS256"

    # 项目路径
    BASE_DIR: str = str(BACKEND_DIR)
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")
    DEFAULT_ICON_DIR: str = os.path.join(STATIC_DIR, "default_icon")
    UPLOAD_ICONS_DIR: str = os.path.join(STATIC_DIR, "upload", "icon")
    UPLOAD_ICONS_LOCAL_DIR: str = "static/upload/icon/"
    STANDS_DIR: str = os.path.join(STATIC_DIR, "stands")
    STANDS_LOCAL_DIR: str = "static/stands/"
    STAND_EXT: str = "png"
    CHARACTER_AVATOR_DIR: str = os.path.join(STATIC_DIR, "character_avator")
    CHARACTER_AVATOR_LOCAL_DIR: str = "static/character_avator"
    CHARACTER_AVATOR_EXT: str = "png"
    GENERATED_AUDIO_DIR: str = os.path.join(STATIC_DIR, "gen_audios")
    GENERATED_AUDIO_LOCAL_DIR: str = "static/gen_audios"

    # 密码加密
    SALT_LENGTH: int = 12

    # 邮箱配置
    MAIL_SERVER: str = Field(default="smtp.163.com", validation_alias="MAIL_SERVER")
    MAIL_PORT: int = Field(default=465, validation_alias="MAIL_PORT", ge=0, le=65535)
    MAIL_USE_SSL: bool = Field(default=True, validation_alias="MAIL_USE_SSL")
    MAIL_USE_TLS: bool = Field(default=False, validation_alias="MAIL_USE_TLS")
    MAIL_USERNAME: str = Field(default="", validation_alias="MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(default="", validation_alias="MAIL_PASSWORD")
    CODE_TIMEOUT: int = Field(default=300, validation_alias="CODE_TIMEOUT")
    CODE_REDIS_KEY_PERFIX: str = Field(default="email_code:", validation_alias="CODE_REDIS_KEY_PREFIX")

    # GPT-SoVITS 配置
    SOVITS_ADDR: str = Field(default="http://127.0.0.1:9880", validation_alias="SOVITS_ADDR")

    POSTGRES_SERVICE_NAME: str = Field(default="", validation_alias="POSTGRES_SERVICE_NAME")
    POSTGRES_BIN_DIR: str = Field(default="", validation_alias="POSTGRES_BIN_DIR")
    POSTGRES_DATA_DIR: str = Field(default="", validation_alias="POSTGRES_DATA_DIR")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return _build_postgres_uri(
            "postgresql+asyncpg",
            self.DATABASE_USER,
            self.DATABASE_PD,
            self.DATABASE_HOST,
            self.DATABASE_PORT,
            self.DATABASE_NAME,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SOVITS_SET_GPT_API(self) -> str:
        return self.SOVITS_ADDR + "/set_gpt_weights"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SOVITS_SET_VIT_API(self) -> str:
        return self.SOVITS_ADDR + "/set_sovits_weights"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SOVITS_TTS_API(self) -> str:
        return self.SOVITS_ADDR + "/tts"
