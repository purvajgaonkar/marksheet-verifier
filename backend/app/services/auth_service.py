"""
auth_service.py
===============

Authentication utilities (Phase 9): password hashing and JWT access tokens.

  * Passwords are hashed with bcrypt via passlib (never stored in plaintext).
  * Access tokens are signed JWTs (python-jose) using config.JWT_SECRET_KEY.

Nothing here logs or returns the raw password or the secret key.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app import config

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# bcrypt only uses the first 72 BYTES of a password. Longer inputs raise in some
# bcrypt versions, so we truncate to 72 bytes for both hashing and verifying.
def _truncate(password: str) -> str:
    return password.encode("utf-8")[:72].decode("utf-8", "ignore")


def hash_password(password: str) -> str:
    """Return a secure bcrypt hash of the password."""
    return _pwd_context.hash(_truncate(password))


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """Return True if the plaintext matches the stored hash. Never raises."""
    if not hashed_password:
        return False
    try:
        return _pwd_context.verify(_truncate(plain_password), hashed_password)
    except Exception:  # noqa: BLE001 - malformed hash etc. -> not a match
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT. `data` should include a 'sub' (the user id)."""
    to_encode = dict(data)
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode/verify a JWT. Returns the claims dict, or None if invalid/expired."""
    try:
        return jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    except JWTError:
        return None
