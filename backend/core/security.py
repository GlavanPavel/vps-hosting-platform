import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt

from core.config import config


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


def _create_token(user_id: int, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id), "type": token_type, "jti": uuid4().hex,
        "iat": now, "exp": now + expires_delta,
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(user_id, "access", timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(user_id: int) -> str:
    return _create_token(user_id, "refresh", timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str, expected_type: str = "access") -> int:
    payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"expected a {expected_type} token")
    return int(payload["sub"])


def decode_access_token(token: str) -> int:
    return decode_token(token, "access")
