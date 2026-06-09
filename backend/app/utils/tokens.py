from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt

from ..core.config import settings
from ..core.exceptions import AppException


def create_access_token(subject: str, role: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload: dict[str, Any] = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise AppException("TOKEN_EXPIRED", "Token da het han.", status_code=401) from exc
    except JWTError as exc:
        raise AppException("INVALID_TOKEN", "Token khong hop le.", status_code=401) from exc
