"""Vinos: the shop's wine catalogue (session 9: Vinoselección, CookinerApp is its sales agent).

The same cellar for every notebook and every plan: nobody creates, edits or deletes wines from
the app; `scripts.sync_vinoseleccion` fills it and keeps prices and stock up to date. Each
person marks favourites, and each notebook recommends wines for its recipes
(/recipes/{id}/wines). Every wine carries `shop_url`: its page in the shop with the agent's
code.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.models import Wine
from app.schemas.auth import MessageResponse
from app.schemas.catalog import Named, texts
from app.schemas.wine import (
    WineCategoryCount,
    WineCategoryRef,
    WineOut,
    WineRecipeOut,
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
        **texts(category),
        slug=category.slug,
        parent=Named.model_validate(category.parent) if category.parent else None,
        serving_temp=category.serving_temp,
    )


def _summary_fields(wine: Wine, favorites: set[int]) -> dict:
    return {
        "id": wine.id,
        "name": wine.name,
        "winery": wine.winery,
        "category": category_ref(wine.category),
        "appellation": wine.appellation,
        "vintage": wine.vintage,
        "price_range": wine.price_range,
        "image_url": wine.image_url,
        "source_name": wine.source_name,
        "source_price": float(wine.source_price) if wine.source_price is not None else None,
        "in_stock": wine.in_stock,
        "shop_url": wine_service.shop_url(wine.source_url),
        "is_favorite": wine.id in favorites,
    }


def to_summary(wine: Wine, favorites: set[int]) -> WineSummary:
    return WineSummary(**_summary_fields(wine, favorites))


def to_out(wine: Wine, favorites: set[int], db=None) -> WineOut:
    paired = wine_service.categories_paired_with(db, wine.category_id) if db is not None else []
    return WineOut(
        **_summary_fields(wine, favorites),
        pairs_with_categories=[Named.model_validate(c) for c in paired],
        sweetness=wine.sweetness,
        body=wine.body,
        ageing=wine.ageing,
        country=wine.country,
        grapes=wine.grapes,
        tasting_notes=wine.tasting_notes,
        pairing_notes=wine.pairing_notes,
        checked_at=wine.checked_at,
    )


def _load(db, lang, wine_id: int) -> Wine:
    try:
        return wine_service.get(db, wine_id)
    except wine_service.WineNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("wine_not_found", lang)) from None


@router.get("", response_model=WineSearchResult)
def search_wines(
    db: DbSession,
    user: CurrentUser,
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
    in_stock: bool = Query(default=False, description="Only what the shop sells now"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> WineSearchResult:
    """The shop's wines, those in stock first. Sold-out ones stay findable (a recipe may
    recommend them) and come marked."""
    filters = wine_service.WineFilters(
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
        in_stock_only=in_stock,
    )
    total, wines = wine_service.search(db, filters, limit=limit, offset=offset)
    starred = wine_service.favorite_ids(db, user.id, [w.id for w in wines])
    return WineSearchResult(total=total, items=[to_summary(w, starred) for w in wines])


@router.get("/category-counts", response_model=list[WineCategoryCount])
def category_counts(db: DbSession, user: CurrentUser) -> list[WineCategoryCount]:
    """Wines in stock per type (a first-level type counts its subtypes), for Por tipos."""
    counts = wine_service.category_counts(db)
    return [WineCategoryCount(category_id=c, count=n) for c, n in sorted(counts.items())]


@router.get("/{wine_id}", response_model=WineOut)
def get_wine(wine_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> WineOut:
    wine = _load(db, lang, wine_id)
    return to_out(wine, wine_service.favorite_ids(db, user.id, [wine.id]), db)


@router.get("/{wine_id}/recipes", response_model=list[WineRecipeOut])
def wine_recipes(
    wine_id: int,
    db: DbSession,
    user: CurrentUser,
    lang: Lang,
    notebook_id: int | None = Query(default=None, description="Default: your own notebook"),
) -> list[WineRecipeOut]:
    """The recipes of a notebook this wine is recommended for, with the reason."""
    wine = _load(db, lang, wine_id)
    try:
        notebook = permissions.resolve_notebook(db, user, notebook_id, edit=False)
    except (permissions.NotebookNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("notebook_not_found", lang)) from None
    return [
        WineRecipeOut(
            link_id=link.id,
            recipe_id=link.recipe_id,
            title=link.recipe.title,
            reason=link.reason,
            added_by=permissions.added_by(notebook, link.added_by),
        )
        for link in wine_service.recipes_of(db, wine, notebook.id)
    ]


@router.post("/{wine_id}/favorite", response_model=MessageResponse)
def add_favorite(wine_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    wine = _load(db, lang, wine_id)
    wine_service.set_favorite(db, user, wine, on=True)
    return MessageResponse(message=t("favorite_added", lang))


@router.delete("/{wine_id}/favorite", response_model=MessageResponse)
def remove_favorite(wine_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    wine = _load(db, lang, wine_id)
    wine_service.set_favorite(db, user, wine, on=False)
    return MessageResponse(message=t("favorite_removed", lang))
