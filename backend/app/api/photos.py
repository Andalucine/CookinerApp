"""Fotos (session 9): photos taken with the phone for a recipe, a wine, a pantry item or a
shopping line. The API keeps the file and answers with the address to store in `image_url`.
In development the files live in a folder of the Mac (`uploads/`, outside git); when the app
is deployed they will go to a file store in the cloud (decision, session 9)."""

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.deps import CurrentUser, Lang
from app.i18n import t
from app.schemas.photo import PhotoOut
from app.services import photo as photo_service

router = APIRouter(prefix="/photos", tags=["photos"])


@router.post("", response_model=PhotoOut, status_code=status.HTTP_201_CREATED)
async def upload_photo(file: UploadFile, user: CurrentUser, lang: Lang) -> PhotoOut:
    """A JPEG, PNG, WebP or HEIC of up to 10 MB → `{"url": "/photos/….jpg"}`."""
    data = await file.read(photo_service.MAX_BYTES + 1)
    try:
        name = photo_service.save(data, file.content_type, file.filename)
    except photo_service.NotAPhoto:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, t("photo_type", lang)) from None
    except photo_service.TooBig:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, t("photo_size", lang)) from None
    return PhotoOut(url=f"/photos/{name}")


@router.get("/{name}")
def get_photo(name: str, lang: Lang) -> FileResponse:
    """The photo itself. No login: the phone shows it with a plain image tag."""
    path = photo_service.path_of(name)
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang))
    return FileResponse(path)
