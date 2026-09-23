"""Recipes: create, read, update, delete, search and favourites; their spices and wines."""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.wines import category_ref, check_plan
from app.api.wines import to_summary as wine_summary
from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.models import Favorite, Recipe
from app.schemas.auth import MessageResponse
from app.schemas.catalog import Named, OccasionOut, SeasonOut, TagOut
from app.schemas.recipe import (
    AuthorOut,
    RecipeCategoryOut,
    RecipeCreate,
    RecipeIn,
    RecipeIngredientOut,
    RecipeOut,
    RecipeSearchResult,
    RecipeSummary,
)
from app.schemas.spice import RecipeSpiceOut
from app.schemas.wine import (
    PairingRuleOut,
    PairingSuggestion,
    RecipeWineIn,
    RecipeWineOut,
    RecipeWinesOut,
)
from app.services import permissions
from app.services import recipe as recipe_service
from app.services import spice as spice_service
from app.services import wine as wine_service

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _categories(recipe: Recipe) -> list[RecipeCategoryOut]:
    return [
        RecipeCategoryOut(
            id=rc.category.id,
            slug=rc.category.slug,
            name_es=rc.category.name_es,
            name_en=rc.category.name_en,
            is_primary=rc.is_primary,
        )
        for rc in recipe.categories
    ]


def _summary_fields(recipe: Recipe, favorites: set[int]) -> dict:
    cats = _categories(recipe)
    primary = next((c for c in cats if c.is_primary), cats[0] if cats else None)
    owner_id = recipe.notebook.owner_id
    return {
        "id": recipe.id,
        "notebook_id": recipe.notebook_id,
        "title": recipe.title,
        "prep_time_minutes": recipe.prep_time_minutes,
        "time_label": recipe_service.time_label(recipe.prep_time_minutes),
        "image_url": recipe.image_url,
        "cook_name": recipe.cook_name,
        "source_type": recipe.source_type,
        "author": AuthorOut.model_validate(recipe.author) if recipe.author else None,
        "added_by": (
            recipe.author.display_name if recipe.author and recipe.author_id != owner_id else None
        ),
        "primary_category": primary,
        "is_favorite": recipe.id in favorites,
        "_categories": cats,
    }


def to_summary(recipe: Recipe, favorites: set[int]) -> RecipeSummary:
    fields = _summary_fields(recipe, favorites)
    fields.pop("_categories")
    return RecipeSummary(**fields)


def to_out(recipe: Recipe, favorites: set[int]) -> RecipeOut:
    fields = _summary_fields(recipe, favorites)
    cats = fields.pop("_categories")
    return RecipeOut(
        **fields,
        description=recipe.description,
        instructions=recipe.instructions,
        servings=recipe.servings,
        source_name=recipe.source_name,
        source_url=recipe.source_url,
        youtube_url=recipe.youtube_url,
        language=recipe.language,
        ingredients=[
            RecipeIngredientOut(
                ingredient_id=ri.ingredient_id,
                name=ri.ingredient.name,
                quantity=float(ri.quantity) if ri.quantity is not None else None,
                unit=ri.unit,
                raw_text=ri.raw_text,
                position=ri.position,
            )
            for ri in recipe.ingredients
        ],
        categories=cats,
        tags=[TagOut.model_validate(x) for x in recipe.tags],
        seasons=[SeasonOut.model_validate(x) for x in recipe.seasons],
        occasions=[OccasionOut.model_validate(x) for x in recipe.occasions],
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
    )


def _load(db, user, lang, recipe_id: int, *, edit: bool) -> Recipe:
    try:
        recipe = recipe_service.get(db, recipe_id)
    except recipe_service.RecipeNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("recipe_not_found", lang)) from None
    try:
        if edit:
            permissions.require_edit(db, user, recipe.notebook)
        else:
            permissions.require_view(db, user, recipe.notebook)
    except permissions.Forbidden:
        # Someone without access must not learn whether the recipe exists
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("recipe_not_found", lang)) from None
    return recipe


@router.post("", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
def create_recipe(body: RecipeCreate, db: DbSession, user: CurrentUser, lang: Lang) -> RecipeOut:
    """Add a recipe to your notebook, or to a notebook where you are editor."""
    notebook = user.notebook
    if body.notebook_id and body.notebook_id != notebook.id:
        try:
            notebook = permissions.get_notebook(db, body.notebook_id)
            permissions.require_edit(db, user, notebook)
        except (permissions.NotebookNotFound, permissions.Forbidden):
            raise HTTPException(status.HTTP_403_FORBIDDEN, t("forbidden", lang)) from None
    try:
        recipe = recipe_service.create(
            db,
            user,
            notebook.id,
            notebook.owner,
            RecipeIn(**body.model_dump(exclude={"notebook_id"})),
        )
    except recipe_service.RecipeLimitReached:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("recipe_limit_reached", lang)) from None
    except recipe_service.UnknownReference:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, t("invalid_reference", lang)
        ) from None
    return to_out(recipe, set())


@router.get("", response_model=RecipeSearchResult)
def search_recipes(
    db: DbSession,
    user: CurrentUser,
    lang: Lang,
    notebook_id: int | None = Query(default=None, description="Default: your own notebook"),
    all_notebooks: bool = Query(default=False, description="Search every notebook you can see"),
    q: str | None = None,
    ingredients: str | None = Query(default=None, description="Comma-separated, all required"),
    max_minutes: int | None = None,
    time: str | None = Query(default=None, pattern="^(quick|medium|long)$"),
    cook: str | None = None,
    source_type: str | None = Query(default=None, pattern="^(own|web|book|family|other)$"),
    source: str | None = None,
    season_id: int | None = None,
    occasion_id: int | None = None,
    category_id: int | None = None,
    tag_ids: str | None = Query(default=None, description="Comma-separated ids, all required"),
    favorites: bool = False,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> RecipeSearchResult:
    if all_notebooks:
        notebook_ids = permissions.accessible_notebook_ids(db, user)
    elif notebook_id and notebook_id != user.notebook.id:
        try:
            permissions.require_view(db, user, permissions.get_notebook(db, notebook_id))
        except (permissions.NotebookNotFound, permissions.Forbidden):
            raise HTTPException(status.HTTP_404_NOT_FOUND, t("notebook_not_found", lang)) from None
        notebook_ids = [notebook_id]
    else:
        notebook_ids = [user.notebook.id]

    filters = recipe_service.SearchFilters(
        notebook_ids=notebook_ids,
        text=q,
        ingredients=[s for s in ingredients.split(",") if s.strip()] if ingredients else None,
        max_minutes=max_minutes,
        time=time,
        cook=cook,
        source_type=source_type,
        source=source,
        season_id=season_id,
        occasion_id=occasion_id,
        category_id=category_id,
        tag_ids=[int(s) for s in tag_ids.split(",") if s.strip()] if tag_ids else None,
        favorites_of=user.id if favorites else None,
    )
    total, recipes = recipe_service.search(db, filters, limit=limit, offset=offset)
    starred = recipe_service.favorite_ids(db, user.id, [r.id for r in recipes])
    return RecipeSearchResult(total=total, items=[to_summary(r, starred) for r in recipes])


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> RecipeOut:
    recipe = _load(db, user, lang, recipe_id, edit=False)
    return to_out(recipe, recipe_service.favorite_ids(db, user.id, [recipe.id]))


@router.get("/{recipe_id}/spices", response_model=list[RecipeSpiceOut])
def recipe_spices(
    recipe_id: int, db: DbSession, user: CurrentUser, lang: Lang
) -> list[RecipeSpiceOut]:
    """The ingredients of the recipe that have a spice card, whether I have them in MY pantry
    and, for each substitute, whether I have it: "no tienes comino, pero sí alcaravea"."""
    recipe = _load(db, user, lang, recipe_id, edit=False)
    return spice_service.recipe_spices(db, recipe, user.notebook.id)


def _recipe_wines(db, user, recipe: Recipe) -> RecipeWinesOut:
    links = wine_service.recipe_wines(db, recipe)
    starred = wine_service.favorite_ids(db, user.id, [link.wine_id for link in links])
    recommended = [
        RecipeWineOut(
            id=link.id,
            wine=wine_summary(link.wine, starred),
            reason=link.reason,
            origin=link.origin,
            added_by=permissions.added_by(recipe.notebook, link.added_by),
        )
        for link in links
    ]
    suggestion = None
    if not recommended:
        found = wine_service.suggest(db, recipe)
        if found is not None:
            starred = wine_service.favorite_ids(db, user.id, [w.id for w in found.wines])
            suggestion = PairingSuggestion(
                based_on=Named.model_validate(found.based_on),
                wine_types=[
                    PairingRuleOut(
                        wine_category=category_ref(r.wine_category),
                        reason_es=r.reason_es,
                        reason_en=r.reason_en,
                    )
                    for r in found.rules
                ],
                my_wines=[wine_summary(w, starred) for w in found.wines],
            )
    return RecipeWinesOut(recommended=recommended, suggestion=suggestion)


@router.get("/{recipe_id}/wines", response_model=RecipeWinesOut)
def recipe_wines(recipe_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> RecipeWinesOut:
    """Wines recommended for the recipe with their reason. When it has none, the automatic
    suggestion: wine types from the pairing rules and the notebook's wines of those types."""
    recipe = _load(db, user, lang, recipe_id, edit=False)
    check_plan(recipe.notebook, lang)
    return _recipe_wines(db, user, recipe)


@router.post(
    "/{recipe_id}/wines", response_model=RecipeWinesOut, status_code=status.HTTP_201_CREATED
)
def add_recipe_wine(
    recipe_id: int, body: RecipeWineIn, db: DbSession, user: CurrentUser, lang: Lang
) -> RecipeWinesOut:
    """Recommend a wine of the same notebook for this recipe, with the reason (owner or editor).
    Sending the same wine again updates the reason."""
    recipe = _load(db, user, lang, recipe_id, edit=True)
    check_plan(recipe.notebook, lang)
    try:
        wine_service.add_to_recipe(db, user, recipe, body.wine_id, body.reason)
    except wine_service.WineInOtherNotebook:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, t("wine_other_notebook", lang)
        ) from None
    return _recipe_wines(db, user, recipe)


@router.delete("/{recipe_id}/wines/{link_id}", response_model=MessageResponse)
def remove_recipe_wine(
    recipe_id: int, link_id: int, db: DbSession, user: CurrentUser, lang: Lang
) -> MessageResponse:
    """Only the notebook owner or whoever recommended it. The wine stays in the notebook."""
    recipe = _load(db, user, lang, recipe_id, edit=True)
    check_plan(recipe.notebook, lang)
    try:
        link = wine_service.get_recipe_wine(db, recipe, link_id)
    except wine_service.RecipeWineNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("wine_not_found", lang)) from None
    if not permissions.can_delete(user, recipe.notebook, link.added_by_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("forbidden", lang))
    wine_service.remove_from_recipe(db, link)
    return MessageResponse(message=t("recipe_wine_removed", lang))


@router.put("/{recipe_id}", response_model=RecipeOut)
def update_recipe(
    recipe_id: int, body: RecipeIn, db: DbSession, user: CurrentUser, lang: Lang
) -> RecipeOut:
    """Owner or editor. An editor's changes are recorded as contributions."""
    recipe = _load(db, user, lang, recipe_id, edit=True)
    try:
        recipe = recipe_service.update(db, recipe, user, body)
    except recipe_service.UnknownReference:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, t("invalid_reference", lang)
        ) from None
    return to_out(recipe, recipe_service.favorite_ids(db, user.id, [recipe.id]))


@router.delete("/{recipe_id}", response_model=MessageResponse)
def delete_recipe(recipe_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    """Only the notebook owner or the recipe's author can delete it."""
    recipe = _load(db, user, lang, recipe_id, edit=True)
    if user.id not in (recipe.notebook.owner_id, recipe.author_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("forbidden", lang))
    recipe_service.delete(db, recipe)
    return MessageResponse(message=t("recipe_deleted", lang))


@router.post("/{recipe_id}/favorite", response_model=MessageResponse)
def add_favorite(recipe_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    recipe = _load(db, user, lang, recipe_id, edit=False)
    existing = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.recipe_id == recipe.id)
    )
    if existing is None:
        db.add(Favorite(user_id=user.id, recipe_id=recipe.id))
        db.commit()
    return MessageResponse(message=t("favorite_added", lang))


@router.delete("/{recipe_id}/favorite", response_model=MessageResponse)
def remove_favorite(
    recipe_id: int, db: DbSession, user: CurrentUser, lang: Lang
) -> MessageResponse:
    existing = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.recipe_id == recipe_id)
    )
    if existing is not None:
        db.delete(existing)
        db.commit()
    return MessageResponse(message=t("favorite_removed", lang))
