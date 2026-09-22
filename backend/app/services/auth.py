"""Business logic for registration, login and password reset."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    generate_reset_code,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import Notebook, PasswordResetToken, User
from app.models.user import PLAN_FREE, PLAN_LIMITS

logger = logging.getLogger(__name__)


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class InvalidResetCode(Exception):
    pass


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def register(db: Session, email: str, display_name: str, password: str, language: str) -> User:
    """Create the account on the free plan together with its personal notebook."""
    if get_user_by_email(db, email):
        raise EmailAlreadyRegistered
    limits = PLAN_LIMITS[PLAN_FREE]
    user = User(
        email=email.lower(),
        display_name=display_name.strip(),
        password_hash=hash_password(password),
        language=language,
        plan=PLAN_FREE,
        max_recipes=limits["max_recipes"],
        max_shared_with=limits["max_shared_with"],
    )
    db.add(user)
    db.flush()  # gives user.id
    if language == "en":
        name = f"{user.display_name}'s notebook"
    else:
        name = f"Cuaderno de {user.display_name}"
    db.add(Notebook(owner_id=user.id, name=name))
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise InvalidCredentials
    if not user.is_active:
        raise InvalidCredentials
    return user


def request_password_reset(db: Session, email: str) -> str | None:
    """Create a reset code for the user. Returns the code (to be emailed), or None if no user.

    Sending the email is not implemented yet: in development the code is written to the log.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    code = generate_reset_code()
    expires = datetime.now(UTC) + timedelta(minutes=get_settings().password_reset_expire_minutes)
    db.add(PasswordResetToken(user_id=user.id, token_hash=hash_token(code), expires_at=expires))
    db.commit()
    logger.info("Password reset code for %s: %s", user.email, code)
    return code


def reset_password(db: Session, email: str, code: str, new_password: str) -> None:
    user = get_user_by_email(db, email)
    if not user:
        raise InvalidResetCode
    token = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.token_hash == hash_token(code),
            PasswordResetToken.used_at.is_(None),
        )
    )
    if not token:
        raise InvalidResetCode
    expires_at = token.expires_at
    if expires_at.tzinfo is None:  # SQLite (tests) returns naive datetimes
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        raise InvalidResetCode
    user.password_hash = hash_password(new_password)
    token.used_at = datetime.now(UTC)
    db.commit()
