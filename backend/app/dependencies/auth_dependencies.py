"""
auth_dependencies.py
====================

FastAPI dependencies for authentication + role-based access control (Phase 9).

  * get_current_user        - require a valid JWT and an active user
  * get_optional_user       - return the user if a valid token is present, else None
  * require_role(*roles)    - factory: require the user to have one of the roles
  * require_admin_or_reviewer
  * require_student

The token is read from the standard `Authorization: Bearer <token>` header.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_db
from app.models import db_models as m
from app.services import auth_service

# auto_error=False so we can return our own 401 (and support optional auth).
_bearer = HTTPBearer(auto_error=False)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated.",
    headers={"WWW-Authenticate": "Bearer"},
)


def _user_from_credentials(
    credentials: Optional[HTTPAuthorizationCredentials], db
) -> Optional[m.User]:
    if credentials is None or not credentials.credentials:
        return None
    payload = auth_service.decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        return None
    user = db.get(m.User, user_id)
    if user is None or not user.is_active:
        return None
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db=Depends(get_db),
) -> m.User:
    """Require a valid token + active user, else 401."""
    user = _user_from_credentials(credentials, db)
    if user is None:
        raise _CREDENTIALS_ERROR
    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db=Depends(get_db),
) -> Optional[m.User]:
    """Return the user if a valid token is present, otherwise None (no error)."""
    return _user_from_credentials(credentials, db)


def require_role(*roles: str):
    """Dependency factory: require the current user to have one of `roles`."""

    def _checker(user: m.User = Depends(get_current_user)) -> m.User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return user

    return _checker


# Ready-made dependencies for the common role checks.
require_admin_or_reviewer = require_role("admin", "reviewer")
require_student = require_role("student")
