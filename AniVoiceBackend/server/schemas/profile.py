from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from .common import MetaResponse


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
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    uid: Optional[int] = None
    salt: Optional[str] = None
    signature: Optional[str] = None
    profile_banner: Optional[str] = None
    birthday: Optional[date] = None
    gender: Optional[str] = None

    model_config = {"from_attributes": True}


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
        if value in (None, ""):
            return value
        datetime.strptime(value, "%Y-%m-%d")
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> Optional[str]:
        if value in (None, "", "male", "female", "private"):
            return value
        raise ValueError("gender must be one of '', 'male', 'female', 'private'")


class ProfileUploadResponse(BaseModel):
    meta: MetaResponse
    profile: Optional[UserProfilePayload] = None
    asset_url: Optional[str] = None
