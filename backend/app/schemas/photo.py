"""A photo kept by the API (session 9)."""

from pydantic import BaseModel


class PhotoOut(BaseModel):
    url: str  # relative to the API: "/photos/1f3….jpg"; the app adds the API address
