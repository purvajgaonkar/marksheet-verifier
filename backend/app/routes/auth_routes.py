"""
auth_routes.py
==============

Authentication endpoints (Phase 9).

    POST /auth/register  -> create a STUDENT account (public; never admin)
    POST /auth/login     -> verify credentials, return a JWT + safe user info
    GET  /auth/me        -> current user (requires a valid token)
    POST /auth/logout    -> client-side token removal; returns a simple success

Security:
    * Public registration always creates role="student". Admin/reviewer accounts
      are created only via backend/create_admin.py (server-side).
    * Passwords are hashed; the hash is never returned.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.dependencies.auth_dependencies import get_current_user
from app.models import db_models as m
from app.schemas.auth_schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services import auth_service, persistence_service

router = APIRouter(tags=["auth"])


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is inactive.")

    token = auth_service.create_access_token(
        {"sub": str(user.id), "email": user.email, "role": user.role}
    )
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
