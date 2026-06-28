"""
create_admin.py
===============

Create an admin or reviewer account from the command line (Phase 9).

Public registration (POST /auth/register) only ever creates STUDENT accounts, so
admin/reviewer accounts are created here, server-side, by someone with shell
access. No password is ever hardcoded — it is typed interactively (hidden).

Run it from the backend folder:

    cd backend
    python create_admin.py

You will be prompted for an email, full name, role, and password.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

# Make `app` importable when run as `python create_admin.py` from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal  # noqa: E402
from app.init_db import init_db  # noqa: E402
from app.models import db_models as m  # noqa: E402
from app.services import auth_service  # noqa: E402


def main() -> None:
    # Make sure the tables exist (safe to call repeatedly).
    init_db()

    print("Create an admin / reviewer account")
    print("----------------------------------")
    email = input("Email: ").strip().lower()
    if not email:
        print("Email is required. Aborting.")
        return

    full_name = input("Full name: ").strip()

    role = input("Role [admin/reviewer] (default: admin): ").strip().lower() or "admin"
    if role not in ("admin", "reviewer"):
        print(f"Invalid role '{role}'. Using 'admin'.")
        role = "admin"

    password = getpass.getpass("Password (min 8 chars): ")
    if len(password) < 8:
        print("Password must be at least 8 characters. Aborting.")
        return
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match. Aborting.")
        return

    db = SessionLocal()
    try:
        existing = db.query(m.User).filter(m.User.email == email).first()
        if existing is not None:
            print(f"A user with email '{email}' already exists (role={existing.role}).")
            return
        user = m.User(
            email=email,
            full_name=full_name or None,
            role=role,
            hashed_password=auth_service.hash_password(password),
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"\nSuccess: created {role} account for {email}.")
        print("You can now log in from the frontend or POST /auth/login.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
