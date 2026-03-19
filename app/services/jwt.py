from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt

from app.core.config import settings


def _create_token(
    user_id: int,
    role: str,
    email: str,
    token_type: str,
    expires_minutes: int,
    token_version: int,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "email": email,
        "token_type": token_type,
        "tv": token_version,
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, role: str, email: str, token_version: int) -> str:
    return _create_token(
        user_id=user_id,
        role=role,
        email=email,
        token_type="access",
        expires_minutes=settings.jwt_expire_minutes,
        token_version=token_version,
    )


def create_refresh_token(user_id: int, role: str, email: str, token_version: int) -> str:
    return _create_token(
        user_id=user_id,
        role=role,
        email=email,
        token_type="refresh",
        expires_minutes=settings.jwt_refresh_expire_minutes,
        token_version=token_version,
    )


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as error:
        raise ValueError("Token inválido") from error
