"""Notebook, sharing and invitation models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.recipe import AuthorOut


class NotebookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner: AuthorOut
    recipe_count: int
    shared_with: int
    max_shared_with: int | None = None  # None = unlimited


class NotebookRename(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class InvitationCreate(BaseModel):
    role: str = Field(default="viewer", pattern="^(viewer|editor)$")
    email: EmailStr | None = Field(default=None, description="Lock the code to this account")


class InvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    role: str
    invited_email: str | None = None
    expires_at: datetime
    created_at: datetime


class JoinRequest(BaseModel):
    code: str = Field(min_length=8, max_length=8)


class AccessOut(BaseModel):
    """Someone with access to my notebook."""

    user: AuthorOut
    role: str
    granted_at: datetime


class RoleChange(BaseModel):
    role: str = Field(pattern="^(viewer|editor)$")


class SharedNotebookOut(BaseModel):
    """A notebook someone shared with me."""

    id: int
    name: str
    owner: AuthorOut
    role: str
    granted_at: datetime
