import logging
import random
from typing import Optional

from fastapi import status
from fastapi.responses import JSONResponse
from fastapi_mail import MessageSchema

from utils import validate_email

from ..runtime import fast_mail, redis_client, settings


def get_email_code_redis_key(email: str, prefix: str) -> str:
    return f"{prefix}{email.lower()}"


def load_email_code_from_redis(email: str, prefix: str) -> Optional[str]:
    return redis_client.get(get_email_code_redis_key(email, prefix))


def consume_email_code(email: str, code: str, prefix: str) -> tuple[bool, str]:
    redis_key = get_email_code_redis_key(email, prefix)
    cached_code = redis_client.get(redis_key)
    if not cached_code:
        return False, "验证码不存在或已过期"
    if cached_code.strip() != code.strip():
        return False, "验证码错误"
    redis_client.delete(redis_key)
    return True, ""


async def send_verification_code_email(
    email: str,
    subject: str,
    body_builder,
    redis_prefix: str,
) -> JSONResponse | dict:
    if fast_mail is None:
        return JSONResponse(
            content={"code": -1, "message": "邮件服务未配置，请先设置 MAIL_USERNAME 和 MAIL_PASSWORD"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if not validate_email(email):
        return JSONResponse(content={"code": "-1", "message": "邮箱格式错误"}, status_code=400)

    verification_code = "".join(random.choices("0123456789", k=6))
    timeout = settings.CODE_TIMEOUT
    body = body_builder(verification_code, timeout)

    try:
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=body,
            subtype="plain",
        )
        await fast_mail.send_message(message)
        redis_client.setex(
            get_email_code_redis_key(email, redis_prefix),
            timeout,
            verification_code,
        )
        logging.info("verification code sent to %s for prefix %s", email, redis_prefix)
        return {"code": 1, "message": "验证码发送成功"}
    except Exception as exc:
        logging.error("邮件发送失败: %s", exc, exc_info=True)
        return JSONResponse(
            content={"code": -1, "message": f"发送邮件失败: {str(exc)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
