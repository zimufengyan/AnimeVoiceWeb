from typing import Optional

from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator, model_validator
from typing_extensions import Annotated

from .common import MetaResponse


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["email@example.com"])
    password: str = Field(..., examples=["password"])
    salt: str = Field(..., examples=["salt"])

    model_config = {"extra": "forbid"}


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., examples=["email@example.com"])
    username: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=4,
            max_length=10,
            pattern=r"^[\p{L}0-9_&@*~:?<>]+$",
        ),
    ] = Field(..., examples=["username"])
    password: str = Field(..., examples=["password"])
    repassword: Optional[str] = Field(default=None, examples=["password"])
    validation_code: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=6,
            max_length=6,
            pattern=r"^[A-Za-z0-9]+$",
        ),
    ] = Field(..., examples=["123456"])
    salt: str = Field(..., examples=["salt"])

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "username": "validUser12",
                    "password": "strongPassword",
                    "validation_code": "Abc123",
                    "salt": "randomSalt",
                }
            ]
        },
    }

    @model_validator(mode="before")
    @classmethod
    def normalize_payload_keys(cls, data):
        if isinstance(data, dict) and "validationCode" in data and "validation_code" not in data:
            data = dict(data)
            data["validation_code"] = data.pop("validationCode")
        return data

    @field_validator("repassword")
    @classmethod
    def validate_repassword(cls, value: Optional[str], info):
        if value in (None, ""):
            return value
        password = info.data.get("password") if info and info.data else None
        if password is not None and value != password:
            raise ValueError("repassword must be the same as password")
        return value


class LoginRegisterResponse(BaseModel):
    meta: MetaResponse
    username: str = ""
    avatar: str = ""
    uid: Optional[int | str] = ""
    rate: Optional[str] = ""
    token: Optional[str] = None


class GetSaltResponse(BaseModel):
    meta: MetaResponse
    salt: str = ""


class EmailCodeRequest(BaseModel):
    email: EmailStr = Field(..., examples=["email@example.com"])


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., examples=["email@example.com"])
    password: str = Field(..., examples=["password"])
    validation_code: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=6,
            max_length=6,
            pattern=r"^[A-Za-z0-9]+$",
        ),
    ] = Field(..., examples=["123456"])
    salt: str = Field(..., examples=["salt"])

    @model_validator(mode="before")
    @classmethod
    def normalize_payload_keys(cls, data):
        if isinstance(data, dict) and "validationCode" in data and "validation_code" not in data:
            data = dict(data)
            data["validation_code"] = data.pop("validationCode")
        return data
