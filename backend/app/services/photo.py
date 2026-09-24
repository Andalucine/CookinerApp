"""Keep the photos the phone sends (session 9): one file per photo, named by a random id so
that nobody can guess another person's photo, in the folder `uploads_dir` of the settings."""

import re
import uuid
from pathlib import Path

from app.core.config import get_settings

MAX_BYTES = 10 * 1024 * 1024
# What the phones send: JPEG and PNG from the gallery, HEIC/HEIF from the iPhone camera,
# WebP from Android. Extension by content type; the file is kept as it comes.
_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/heic": "heic",
    "image/heif": "heif",
}
_NAME = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp|heic|heif)$")


class NotAPhoto(Exception):
    pass


class TooBig(Exception):
    pass


def uploads_dir() -> Path:
    folder = Path(get_settings().uploads_dir)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _extension(content_type: str | None, filename: str | None) -> str | None:
    if content_type and content_type.lower() in _EXTENSIONS:
        return _EXTENSIONS[content_type.lower()]
    suffix = (Path(filename).suffix.lower().lstrip(".") if filename else "") or ""
    if suffix == "jpeg":
        suffix = "jpg"
    return suffix if suffix in _EXTENSIONS.values() else None


def _looks_like_an_image(data: bytes) -> bool:
    return (
        data.startswith(b"\xff\xd8\xff")  # JPEG
        or data.startswith(b"\x89PNG")
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
        or data[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1", b"ftypheif", b"ftyphevc")
    )


def save(data: bytes, content_type: str | None, filename: str | None) -> str:
    """Keep the bytes and return the file name ("1f3….jpg")."""
    extension = _extension(content_type, filename)
    if extension is None or not _looks_like_an_image(data):
        raise NotAPhoto
    if len(data) > MAX_BYTES:
        raise TooBig
    name = f"{uuid.uuid4().hex}.{extension}"
    (uploads_dir() / name).write_bytes(data)
    return name


def path_of(name: str) -> Path | None:
    """The file of a photo name, or None if the name is not one of ours or it is gone."""
    if not _NAME.match(name):
        return None
    path = uploads_dir() / name
    return path if path.is_file() else None
