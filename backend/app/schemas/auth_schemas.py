"""
auth_schemas.py
===============

Pydantic schemas for authentication (Phase 9).

The hashed password is NEVER part of any response model, so it can't leak.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Body for POST /auth/register. Public registration is forced to 'student'."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    # Accepted but IGNORED for public registration (always student) — see route.
    role: Optional[str] = "student"


class UserLogin(BaseModel):
    """Body for POST /auth/login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Safe user view (no password). Built directly from the ORM User."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[object] = None  # datetime -> ISO string in JSON


class TokenResponse(BaseModel):
    """Returned by POST /auth/login."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SetupAdminRequest(BaseModel):
    """Body for POST /auth/setup-admin (one-time first-admin bootstrap)."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    setup_secret: str = Field(..., min_length=1)


class SetupAdminResponse(BaseModel):
    """Returned by POST /auth/setup-admin."""
    message: str
    user: UserResponse
