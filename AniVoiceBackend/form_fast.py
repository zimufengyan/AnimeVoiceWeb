# for FastAPI.

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
    email: str
    password: str
    salt: str


class TTSRequest(BaseModel):
    text: str
    lang: str = 'zh'
    belong: str
    character: str = Field(default='')

    @model_validator(mode="before")
    @classmethod
    def normalize_character_field(cls, data):
        if isinstance(data, dict) and "character" not in data and "charactor" in data:
            data["character"] = data["charactor"]
        return data


class LoginResponse(BaseModel):
    code: str = '3'     # 结果代码
    username: str = ''
    avatar: str = ''      # 头像地址
    index: Optional[str] = ''      # 用户编号
    rate: Optional[str] = ''       # 评级
    token: Optional[str] = None  
    message: str = ''
