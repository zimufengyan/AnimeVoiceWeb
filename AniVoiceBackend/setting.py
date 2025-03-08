import os
from datetime import timedelta

from pydantic_settings import BaseSettings


class Config:
    # IP地址
    HOST: str = "10.60.102.53"
    PORT: int = 25683

    # Postgres 数据库配置
    DATABASE_NAME: str = "postgres"
    USERTABLE_NAME: str = 'userinfo'
    DATABASE_USER: str = "postgres"
    DATABASE_PD: str = "12345678"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    SECRET_KEY: str = 'ohlamamahaha0520@#$'
    SQLALCHEMY_DATABASE_URI: str = f'postgresql://{DATABASE_USER}:{DATABASE_PD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 2        # Redis 数据库编号

    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(days=1)
    JWT_SECRET_KEY: str = 'ohlamamahaha0520@#$'
    
    # 项目路径
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    # 静态文件夹的路径
    STATIC_DIR: str = os.path.join(BASE_DIR, 'static')
    # 默认头像的路径
    DEFAULT_ICON_DIR: str = os.path.join(STATIC_DIR, 'default_icon')
    # 头像的上传目录
    UPLOAD_ICONS_DIR: str = os.path.join(STATIC_DIR, 'upload', 'icon')
    UPLOAD_ICONS_LOCAL_DIR: str = "static/upload/icon/"
    # 立绘图像目录
    STANDS_DIR: str = os.path.join(STATIC_DIR, "stands")
    STANDS_LOCAL_DIR: str = "static/stands/"
    STAND_EXT: str = "png"
    # 角色头像目录
    CHARACTER_AVATOR_DIR: str = os.path.join(STATIC_DIR, 'character_avator')
    CHARACTER_AVATOR_LOCAL_DIR: str = "/static/character_avator"
    CHARACTER_AVATOR_EXT: str = "png"
    # 生成的语音存放目录
    GENERATED_AUDIO_DIR: str = os.path.join(STATIC_DIR, 'gen_audios')
    GENERATED_AUDIO_LOCAL_DIR: str = "/static/gen_audios"

    # flask-session的配置
    # PERMANENT_SESSION_LIFETIME = timedelta(days=14)	#过期时间

    # 密码加密
    SALT_LENGTH: int = 12    # 盐值长度

    # 邮箱配置
    MAIL_SERVER: str = "smtp.163.com"
    MAIL_PORT: int = 465
    MAIL_USE_SSL: bool = True
    MAIL_USERNAME: str = "zimufengyan@163.com"
    MAIL_PASSWORD: str = "PWtKDUVYZFxnpJvf"
    CODE_TIMEOUT: int = 300      # 验证码有效期, 单位为秒
    CODE_REDIS_KEY_PERFIX: str = "email_code:"       # Redis中的邮箱验证码键的前缀

    # GPT-SoVITS 配置
    SOVITS_ADDR: str = "http://127.0.0.1:9880"
    SOVITS_SET_GPT_API: str = SOVITS_ADDR + "/set_gpt_weights"
    SOVITS_SET_VIT_API: str = SOVITS_ADDR + "/set_sovits_weights"
    SOVITS_TTS_API: str = SOVITS_ADDR + "/tts"


class DevelopmentConfig(Config):
    ENV: str = 'development'
    DEBUG: bool = True


class ProductionConfig(Config):
    ENV = 'production'
    DDEBUG = False


class Settings(BaseSettings):
    # for FastAPI
    # IP地址
    HOST: str = "10.60.102.53"
    PORT: int = 25683

    # Postgres 数据库配置
    DATABASE_NAME: str = "postgres"
    USERTABLE_NAME: str = 'userinfo'
    DATABASE_USER: str = "postgres"
    DATABASE_PD: str = os.getenv("POSTGRES_PASSWORD")
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: str = f'postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 2        # Redis 数据库编号

    ACCESS_TOKEN_EXPIRES: timedelta = timedelta(days=1)
    SECRET_KEY: str = 'ohlamamahaha0520@#$'
    ALGORITHM: str = "HS256"
    
    # 项目路径
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    # 静态文件夹的路径
    STATIC_DIR: str = os.path.join(BASE_DIR, 'static')
    # 默认头像的路径
    DEFAULT_ICON_DIR: str = os.path.join(STATIC_DIR, 'default_icon')
    # 头像的上传目录
    UPLOAD_ICONS_DIR: str = os.path.join(STATIC_DIR, 'upload', 'icon')
    UPLOAD_ICONS_LOCAL_DIR: str = "static/upload/icon/"
    # 立绘图像目录
    STANDS_DIR: str = os.path.join(STATIC_DIR, "stands")
    STANDS_LOCAL_DIR: str = "static/stands/"
    STAND_EXT: str = "png"
    # 角色头像目录
    CHARACTER_AVATOR_DIR: str = os.path.join(STATIC_DIR, 'character_avator')
    CHARACTER_AVATOR_LOCAL_DIR: str = "static/character_avator"
    CHARACTER_AVATOR_EXT: str = "png"
    # 生成的语音存放目录
    GENERATED_AUDIO_DIR: str = os.path.join(STATIC_DIR, 'gen_audios')
    GENERATED_AUDIO_LOCAL_DIR: str = "static/gen_audios"

    # flask-session的配置
    # PERMANENT_SESSION_LIFETIME = timedelta(days=14)	#过期时间

    # 密码加密
    SALT_LENGTH: int = 12    # 盐值长度

    # 邮箱配置
    MAIL_SERVER: str = "smtp.163.com"
    MAIL_PORT: int = 465
    MAIL_USE_SSL: bool = True
    MAIL_USE_TLS: bool = False
    MAIL_USERNAME: str = "zimufengyan@163.com"
    MAIL_PASSWORD: str = "PWtKDUVYZFxnpJvf"
    CODE_TIMEOUT: int = 300      # 验证码有效期, 单位为秒
    CODE_REDIS_KEY_PERFIX: str = "email_code:"       # Redis中的邮箱验证码键的前缀

    # GPT-SoVITS 配置
    SOVITS_ADDR: str = "http://127.0.0.1:9880"
    SOVITS_SET_GPT_API: str = SOVITS_ADDR + "/set_gpt_weights"
    SOVITS_SET_VIT_API: str = SOVITS_ADDR + "/set_sovits_weights"
    SOVITS_TTS_API: str = SOVITS_ADDR + "/tts"

    class Config:
        # case_sensitive = True
        env_file: str = ".env"
        env_file_encoding: str = "utf-8"