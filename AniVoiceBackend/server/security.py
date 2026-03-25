import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt

from .runtime import oauth2_scheme, redis_client, settings, user_manager


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or settings.ACCESS_TOKEN_EXPIRES)
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, verify_exp: bool = True) -> dict:
    options = None if verify_exp else {"verify_exp": False}
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options=options)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        jti = payload.get("jti")
        if not jti or redis_client.exists(f"blacklist:{jti}"):
            raise credentials_exception

        uid_value = payload.get("sub")
        if uid_value is None:
            raise credentials_exception

        user = await user_manager.get_user_by_uid(int(uid_value))
        if user is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception
    return user
