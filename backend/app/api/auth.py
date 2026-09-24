"""Registration, login, current user (and its language) and password reset."""

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbSession, Lang
from app.core.security import create_access_token
from app.i18n import t
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserPublic, UserUpdate
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id), user=UserPublic.model_validate(user)
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: DbSession, lang: Lang) -> TokenResponse:
    try:
        user = auth_service.register(
            db, body.email, body.display_name, body.password, body.language
        )
    except auth_service.EmailAlreadyRegistered:
        raise HTTPException(status.HTTP_409_CONFLICT, t("email_already_registered", lang)) from None
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession, lang: Lang) -> TokenResponse:
    try:
        user = auth_service.authenticate(db, body.email, body.password)
    except auth_service.InvalidCredentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, t("invalid_credentials", lang)) from None
    return _token_response(user)


@router.get("/me", response_model=UserPublic)
def me(user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(user)


@router.patch("/me", response_model=UserPublic)
def update_me(body: UserUpdate, db: DbSession, user: CurrentUser) -> UserPublic:
    """Mi cuenta: change the language (the app's texts and the API messages follow it)."""
    user.language = body.language
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(body: ForgotPasswordRequest, db: DbSession, lang: Lang) -> MessageResponse:
    # Same answer whether the email exists or not, so nobody can guess registered emails.
    auth_service.request_password_reset(db, body.email)
    return MessageResponse(message=t("reset_code_sent", lang))


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, db: DbSession, lang: Lang) -> MessageResponse:
    try:
        auth_service.reset_password(db, body.email, body.code, body.new_password)
    except auth_service.InvalidResetCode:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, t("reset_code_invalid", lang)) from None
    return MessageResponse(message=t("password_updated", lang))
