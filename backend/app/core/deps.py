"""FastAPI dependencies shared by all routers."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.i18n import t
from app.models import User

DbSession = Annotated[Session, Depends(get_db)]


def get_language(accept_language: Annotated[str | None, Header()] = None) -> str:
    """'es' or 'en' from the Accept-Language header (default es)."""
    if accept_language and accept_language.lower().startswith("en"):
        return "en"
    return "es"


Lang = Annotated[str, Depends(get_language)]


def get_current_user(
    db: DbSession,
    lang: Lang,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, t("not_authenticated", lang))
    user_id = decode_access_token(authorization.split(" ", 1)[1])
    user = db.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, t("not_authenticated", lang))
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_optional_user(
    db: DbSession, authorization: Annotated[str | None, Header()] = None
) -> User | None:
    """The signed-in user when a token comes, None otherwise (public routes that add the
    notebook's own data, like the spice zone with the notebook's blends)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    user_id = decode_access_token(authorization.split(" ", 1)[1])
    user = db.get(User, user_id) if user_id else None
    return user if user and user.is_active else None


OptionalUser = Annotated[User | None, Depends(get_optional_user)]
