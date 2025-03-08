# for FastAPI.

from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str
    salt: str


class TTSRequest(BaseModel):
    text: str
    lang: str = 'zh'
    belong: str
    charactor: str = ''


class LoginResponse(BaseModel):
    code: str = '3'     # 结果代码
    username: str = ''
    avatar: str = ''      # 头像地址
    index: Optional[str] = ''      # 用户编号
    rate: Optional[str] = ''       # 评级
    token: Optional[str] = None  
    message: str = ''