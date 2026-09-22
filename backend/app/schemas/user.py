"""User input/output models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    display_name: str
    language: str
    plan: str
    max_recipes: int | None
    max_shared_with: int | None
    notebook_id: int
    created_at: datetime
