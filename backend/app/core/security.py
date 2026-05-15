from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from app.core.config import settings


ALGORITHM = "HS256"


def _normalize_password_bytes(password: str) -> bytes:
    # bcrypt only processes the first 72 bytes; truncate consistently for hash/verify.
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    password_bytes = _normalize_password_bytes(password)
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    password_bytes = _normalize_password_bytes(password)
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(subject: str, email: str = "") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if email:
        payload["email"] = email
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
