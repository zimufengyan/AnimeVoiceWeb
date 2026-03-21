# for FastAPI.

from typing import List, Optional
from pydantic import AliasChoices, BaseModel, Field, EmailStr, field_validator, StringConstraints 
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, date
from typing_extensions import Annotated
import re



class MetaResponse(BaseModel):
    code: str = '1'     # 结果代码
    message: str = ''
    timestamp: datetime = datetime.now()

    def to_dict(self):
        return asdict(self)


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example='email@example.com')
    password: str = Field(..., example='password')
    salt: str = Field(..., example='salt')
    model_config = {"extra": "forbid"}       # 禁止额外参数


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., example="email@example.com")
    username: Annotated[str, StringConstraints(
        strip_whitespace=True, min_length=4, 
        max_length=10, pattern=r"^[\p{L}0-9_&@*~:?<>]+$")] = Field(..., example="username") # type: ignore
    password: str = Field(..., example="password")
    validation_code: Annotated[str, StringConstraints(
        strip_whitespace=True, min_length=6, 
        max_length=6, pattern=r"^[A-Za-z0-9]+$")] = Field(..., example="123456") # type: ignore
    salt: str = Field(..., example="salt")

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "examples": [{
                "email": "user@example.com",
                "username": "validUser12",
                "password": "strongPassword",
                "validation_code": "Abc123",
                "salt": "randomSalt"
            }]
        }
    }



class TTSRequest(BaseModel):
    text: Annotated[str, StringConstraints(
        strip_whitespace=True, min_length=4, 
        max_length=200)] = Field(..., example='你好，欢迎使用语音合成服务。')
    lang: str = 'zh'
    belong: str
    character: str = Field(
        ...,
        validation_alias=AliasChoices('character', 'charactor'),
        serialization_alias='character',
    )


class LoginRegisterResponse(BaseModel):
    meta: MetaResponse
    username: str = ''
    avatar: str = ''      # 头像地址
    uid: Optional[int | str] = ''      # 用户编号
    rate: Optional[str] = ''       # 评级
    token: Optional[str] = None  


class GetSaltResponse(BaseModel):
    meta: MetaResponse
    salt: str = ''


class GenerateVoiceResponse(BaseModel):
    meta: MetaResponse
    audio_url: str


class BelongStaticsResponse(BaseModel):
    meta: MetaResponse
    stands: List[str]
    avators: List[str]
    names: List[str]


class UserItem(BaseModel):
    id: Optional[int] = None
    name: str
    sex: Optional[int] = None
    age: Optional[int] = None
    pic: Optional[str] = None
    pwd: str
    phone: Optional[str] = None
    email: str
    rate: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    uid: Optional[int] = None
    salt: Optional[str] = None
    signature: Optional[str] = None
    profile_banner: Optional[str] = None
    birthday: Optional[date] = None
    gender: Optional[str] = None

    class Config:
        from_attributes = True


class AudioRecordItem(BaseModel):
    audio_id: int | None = None
    user_id: int
    audio_character: str
    audio_belong: str
    audio_path: str
    created_at: Optional[datetime] = datetime.now()
    audio_text: str = ""
    text_lang: str = "zh"
    character_avator_path: str = ""
    audio_filename: str = ""

    class Config:
        from_attributes = True


class AudioRecordResponse(BaseModel):
    meta: MetaResponse
    records: Optional[List[AudioRecordItem]] = None


class UserProfilePayload(BaseModel):
    username: str = ""
    avatar: str = ""
    uid: int | str | None = None
    rate: str = ""
    signature: str = ""
    profile_banner: str = ""
    birthday: str = ""
    gender: str = ""


class UserProfileResponse(BaseModel):
    meta: MetaResponse
    profile: UserProfilePayload


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    avatar: Optional[str] = None
    signature: Optional[str] = None
    profile_banner: Optional[str] = None
    birthday: Optional[str] = None
    gender: Optional[str] = None

    model_config = {"extra": "forbid"}

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, value: Optional[str]) -> Optional[str]:
        """校验生日字符串是否符合 YYYY-MM-DD 格式。"""
        if value in (None, ""):
            return value
        datetime.strptime(value, "%Y-%m-%d")
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> Optional[str]:
        """限制性别字段只接受前端约定的枚举值。"""
        if value in (None, "", "male", "female", "private"):
            return value
        raise ValueError("gender must be one of '', 'male', 'female', 'private'")


class ProfileUploadResponse(BaseModel):
    meta: MetaResponse
    profile: Optional[UserProfilePayload] = None
    asset_url: Optional[str] = None


@dataclass
class TTSReqForm:
    text: str = None,                   # str.(required) text to be synthesized
    text_lang: str = "auto",            # str.(required) language of the text to be synthesized
    ref_audio_path: str = None,         # str.(required) reference audio path
    prompt_lang: str = None,            # str.(required) language of the prompt text for the reference audio
    prompt_text: str = "",              # str.(optional) prompt text for the reference audio
    top_k: int = 5,                     # int. top k sampling
    top_p: float = 1,                   # float. top p sampling
    temperature: float = 1,             # float. temperature for sampling
    sample_steps: int = 16,             # int. When you use v3 model,you can set this sample_steps
    media_type: str = "wav",            # str. Set the file format for returning audio.
    streaming_mode: bool = False,       # bool. whether to return a streaming response.
    threshold: int = 30                 # int. Text segmentation parameter,the lower value, the faster the streaming inference, but the worse the audio quality.

    def to_dict(self):
        return asdict(self)
