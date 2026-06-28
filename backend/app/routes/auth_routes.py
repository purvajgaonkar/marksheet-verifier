"""
auth_routes.py
==============

Authentication endpoints (Phase 9).

    POST /auth/register     -> create a STUDENT account (public; never admin)
    POST /auth/login        -> verify credentials, return a JWT + safe user info
    GET  /auth/me           -> current user (requires a valid token)
    POST /auth/logout       -> client-side token removal; returns a simple success
    POST /auth/setup-admin  -> one-time first-admin bootstrap (SETUP_SECRET gated)

Security:
    * Public registration always creates role="student". Admin/reviewer accounts
      are created via backend/create_admin.py (server-side) or, once after a
      fresh deploy, via POST /auth/setup-admin.
    * Passwords are hashed; the hash is never returned.
    * No password, token, or secret is ever logged.
"""

from __future__ import annotations

import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app import config
from app.database import get_db
from app.dependencies.auth_dependencies import get_current_user
from app.models import db_models as m
from app.schemas.auth_schemas import (
    SetupAdminRequest,
    SetupAdminResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services import auth_service, persistence_service

router = APIRouter(tags=["auth"])
logger = logging.getLogger("marksheet.auth")


@router.post("/auth/register", response_model=UserResponse, status_code=201)
def register(body: UserCreate, db=Depends(get_db)) -> m.User:
    """Register a STUDENT account. The requested role is ignored (always student)."""
    email = body.email.lower().strip()
    existing = db.query(m.User).filter(m.User.email == email).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = m.User(
        email=email,
        full_name=body.full_name.strip(),
        role="student",  # public registration is ALWAYS a student
        hashed_password=auth_service.hash_password(body.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit (no case, no password/token logged).
    persistence_service.add_audit(
        db, None, "user_registered", f"email={user.email} role=student", user.id
    )
    db.commit()

    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(body: UserLogin, db=Depends(get_db)) -> TokenResponse:
    """Verify email/password and return a JWT access token + safe user info."""
    email = body.email.lower().strip()
    user = db.query(m.User).filter(m.User.email == email).first()
    if user is None or not auth_service.verify_password(body.password, user.hashed_password):
        # Log the failure WITHOUT the password.
        logger.info("Login failed for email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        logger.info("Login blocked (inactive) for email=%s", email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is inactive.")

    token = auth_service.create_access_token(
        {"sub": str(user.id), "email": user.email, "role": user.role}
    )
    logger.info("Login success for user_id=%s role=%s", user.id, user.role)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/auth/me", response_model=UserResponse)
def me(current_user: m.User = Depends(get_current_user)) -> m.User:
    """Return the currently authenticated user."""
    return current_user


@router.post("/auth/logout")
def logout(current_user: m.User = Depends(get_current_user)) -> dict:
    """
    JWT logout is handled client-side by deleting the token. This endpoint just
    confirms the caller is authenticated and returns a success message.
    """
    return {"message": "Logged out. Please discard your access token."}


@router.post("/auth/setup-admin", response_model=SetupAdminResponse)
def setup_admin(body: SetupAdminRequest, db=Depends(get_db)) -> SetupAdminResponse:
    """
    One-time bootstrap for the FIRST admin after a fresh deployment.

    Guards:
        * Disabled unless SETUP_SECRET is configured in the environment.
        * Requires the correct setup_secret (constant-time compared).
        * Refuses if ANY admin or reviewer already exists.

    Never logs or returns the password or the secret.
    """
    # 1) Endpoint disabled unless a setup secret is configured.
    if not config.setup_admin_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin setup is not enabled.",
        )

    # 2) Verify the provided secret (constant-time to avoid timing leaks).
    if not hmac.compare_digest(body.setup_secret, config.SETUP_SECRET):
        logger.warning("setup-admin attempt with an invalid setup secret.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid setup secret.")

    # 3) Only allowed while there is NO usable staff account yet. The demo users
    #    seeded by init_db (admin@demo.local / reviewer@demo.local) have NO
    #    password and cannot log in, so they must NOT count as "already set up".
    staff_exists = (
        db.query(m.User)
        .filter(
            m.User.role.in_(("admin", "reviewer")),
            m.User.hashed_password.isnot(None),
        )
        .first()
        is not None
    )
    if staff_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admin setup is already completed.")

    email = body.email.lower().strip()
    existing = db.query(m.User).filter(m.User.email == email).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = m.User(
        email=email,
        full_name=body.full_name.strip(),
        role="admin",
        hashed_password=auth_service.hash_password(body.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit WITHOUT any sensitive data (no password, no secret).
    persistence_service.add_audit(
        db, None, "setup_admin_created", f"email={user.email} role=admin", user.id
    )
    db.commit()
    logger.info("setup_admin_created: user_id=%s", user.id)

    return SetupAdminResponse(
        message="First admin created successfully",
        user=UserResponse.model_validate(user),
    )
