"""Vinos: the wines of a notebook, with facets and favourites.

The wine section follows the plan of the notebook owner: a free notebook answers 403 with a
message explaining it (after checking access, so strangers still get 404).
The wines recommended for a recipe live in /recipes/{id}/wines.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.models import Notebook, Wine
from app.schemas.auth import MessageResponse
from app.schemas.catalog import Named
from app.schemas.wine import (
    WineCategoryRef,
    WineCreate,
    WineIn,
    WineOut,
    WineSearchResult,
    WineSummary,
)
from app.services import permissions
from app.services import wine as wine_service

router = APIRouter(prefix="/wines", tags=["wines"])


def category_ref(category) -> WineCategoryRef | None:
    if category is None:
        return None
    return WineCategoryRef(
        id=category.id,
        name_es=category.name_es,
        name_en=category.name_en,
        slug=category.slug,
        parent=Named.model_validate(category.parent) if category.parent else None,
        serving_temp=category.serving_temp,
    )


def _summary_fields(wine: Wine, favorites: set[int]) -> dict:
    return {
        "id": wine.id,
        "notebook_id": wine.notebook_id,
        "name": wine.name,
        "winery": wine.winery,
        "category": category_ref(wine.category),
        "appellation": wine.appellation,
        "vintage": wine.vintage,
        "price_range": wine.price_range,
        "image_url": wine.image_url,
        "added_by": permissions.added_by(wine.notebook, wine.added_by),
        "is_favorite": wine.id in favorites,
    }


def to_summary(wine: Wine, favorites: set[int]) -> WineSummary:
    return WineSummary(**_summary_fields(wine, favorites))


def to_out(wine: Wine, favorites: set[int]) -> WineOut:
    return WineOut(
        **_summary_fields(wine, favorites),
        sweetness=wine.sweetness,
        body=wine.body,
        ageing=wine.ageing,
        country=wine.country,
        grapes=wine.grapes,
        tasting_notes=wine.tasting_notes,
        pairing_notes=wine.pairing_notes,
        source_url=wine.source_url,
        edited_by=permissions.added_by(wine.notebook, wine.updated_by),
        created_at=wine.created_at,
        updated_at=wine.updated_at,
    )


def check_plan(notebook: Notebook, lang: str) -> None:
    try:
        wine_service.require_wines(notebook)
    except wine_service.WinesNotInPlan:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("wines_not_in_plan", lang)) from None


def _notebook(db, user, lang, notebook_id: int | None, *, edit: bool) -> Notebook:
    try:
        notebook = permissions.resolve_notebook(db, user, notebook_id, edit=edit)
    except (permissions.NotebookNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("notebook_not_found", lang)) from None
    check_plan(notebook, lang)
    return notebook


def _load(db, user, lang, wine_id: int, *, edit: bool) -> Wine:
    try:
        wine = wine_service.get(db, wine_id)
        if edit:
            permissions.require_edit(db, user, wine.notebook)
        else:
            permissions.require_view(db, user, wine.notebook)
    except (wine_service.WineNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("wine_not_found", lang)) from None
    check_plan(wine.notebook, lang)
    return wine


@router.get("", response_model=WineSearchResult)
def search_wines(
    db: DbSession,
    user: CurrentUser,
    lang: Lang,
    notebook_id: int | None = Query(default=None, description="Default: your own notebook"),
    q: str | None = Query(default=None, description="Name, winery, grapes or appellation"),
    category_id: int | None = Query(default=None, description="A first-level type includes all"),
    sweetness: str | None = None,
    body: str | None = None,
    ageing: str | None = None,
    country: str | None = None,
    appellation: str | None = None,
    grape: str | None = None,
    price_range: str | None = None,
    favorites: bool = False,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> WineSearchResult:
    notebook = _notebook(db, user, lang, notebook_id, edit=False)
    filters = wine_service.WineFilters(
        notebook_ids=[notebook.id],
        text=q,
        category_id=category_id,
        sweetness=sweetness,
        body=body,
        ageing=ageing,
        country=country,
        appellation=appellation,
        grape=grape,
        price_range=price_range,
        favorites_of=user.id if favorites else None,
    )
    total, wines = wine_service.search(db, filters, limit=limit, offset=offset)
    starred = wine_service.favorite_ids(db, user.id, [w.id for w in wines])
    return WineSearchResult(total=total, items=[to_summary(w, starred) for w in wines])


@router.post("", response_model=WineOut, status_code=status.HTTP_201_CREATED)
def create_wine(body: WineCreate, db: DbSession, user: CurrentUser, lang: Lang) -> WineOut:
    """Add a wine to your notebook, or to a notebook where you are editor."""
    notebook = _notebook(db, user, lang, body.notebook_id, edit=True)
    try:
        wine = wine_service.create(db, user, notebook, WineIn(**body.model_dump()))
    except wine_service.UnknownWineCategory:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, t("wine_invalid_reference", lang)
        ) from None
    return to_out(wine, set())


@router.get("/{wine_id}", response_model=WineOut)
def get_wine(wine_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> WineOut:
    wine = _load(db, user, lang, wine_id, edit=False)
    return to_out(wine, wine_service.favorite_ids(db, user.id, [wine.id]))


@router.put("/{wine_id}", response_model=WineOut)
def update_wine(
    wine_id: int, body: WineIn, db: DbSession, user: CurrentUser, lang: Lang
) -> WineOut:
    wine = _load(db, user, lang, wine_id, edit=True)
    try:
        wine = wine_service.update(db, wine, user, body)
    except wine_service.UnknownWineCategory:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, t("wine_invalid_reference", lang)
        ) from None
    return to_out(wine, wine_service.favorite_ids(db, user.id, [wine.id]))


@router.delete("/{wine_id}", response_model=MessageResponse)
def delete_wine(wine_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    """Only the notebook owner or whoever added the wine."""
    wine = _load(db, user, lang, wine_id, edit=True)
    if not permissions.can_delete(user, wine.notebook, wine.added_by_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("forbidden", lang))
    wine_service.delete(db, wine)
    return MessageResponse(message=t("wine_deleted", lang))


@router.post("/{wine_id}/favorite", response_model=MessageResponse)
def add_favorite(wine_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    wine = _load(db, user, lang, wine_id, edit=False)
    wine_service.set_favorite(db, user, wine, on=True)
    return MessageResponse(message=t("favorite_added", lang))


@router.delete("/{wine_id}/favorite", response_model=MessageResponse)
def remove_favorite(wine_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    wine = _load(db, user, lang, wine_id, edit=False)
    wine_service.set_favorite(db, user, wine, on=False)
    return MessageResponse(message=t("favorite_removed", lang))
