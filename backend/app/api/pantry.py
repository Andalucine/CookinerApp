"""Mi despensa: what I have at home and what I can cook with it. Always the user's own notebook."""

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.schemas.auth import MessageResponse
from app.schemas.pantry import (
    CookableRecipe,
    MissingIngredient,
    PantryItemIn,
    PantryItemOut,
    PantryItemPhoto,
    PantryOut,
    WhatCanICookOut,
)
from app.services import pantry as pantry_service
from app.services import recipe as recipe_service

router = APIRouter(prefix="/pantry", tags=["pantry"])


def _out(item) -> PantryItemOut:
    return PantryItemOut(
        id=item.id, ingredient_id=item.ingredient_id, name=item.ingredient.name,
        location=item.location, image_url=item.image_url,
    )  # fmt: skip


@router.get("", response_model=PantryOut)
def get_pantry(db: DbSession, user: CurrentUser) -> PantryOut:
    return PantryOut(items=[_out(i) for i in pantry_service.list_items(db, user.notebook.id)])


@router.post("/items", response_model=PantryItemOut, status_code=status.HTTP_201_CREATED)
def add_pantry_item(body: PantryItemIn, db: DbSession, user: CurrentUser) -> PantryItemOut:
    """Mark an ingredient as available (by name; new names join the catalogue)."""
    item = pantry_service.add_item(db, user.notebook.id, body.name, body.location)
    return _out(item)


@router.patch("/items/{item_id}", response_model=PantryItemOut)
def set_pantry_photo(
    item_id: int, body: PantryItemPhoto, db: DbSession, user: CurrentUser, lang: Lang
) -> PantryItemOut:
    """Put a photo on what I have (or remove it with `image_url: null`)."""
    item = pantry_service.set_item_photo(db, user.notebook.id, item_id, body.image_url)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang))
    return _out(item)


@router.delete("/items/{item_id}", response_model=MessageResponse)
def remove_pantry_item(
    item_id: int, db: DbSession, user: CurrentUser, lang: Lang
) -> MessageResponse:
    if not pantry_service.remove_item(db, user.notebook.id, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang))
    return MessageResponse(message=t("pantry_item_removed", lang))


@router.get("/what-can-i-cook", response_model=WhatCanICookOut)
def what_can_i_cook(db: DbSession, user: CurrentUser) -> WhatCanICookOut:
    """Recipes of my notebook I can make right now, and those one ingredient short."""
    from app.api.recipes import to_summary

    complete, missing_one = pantry_service.what_can_i_cook(db, user.notebook.id)
    all_ids = [r.id for r, _ in complete + missing_one]
    starred = recipe_service.favorite_ids(db, user.id, all_ids)

    def pack(pairs):
        return [
            CookableRecipe(
                recipe=to_summary(r, starred),
                missing=[MissingIngredient(ingredient_id=i.id, name=i.name) for i in missing],
            )
            for r, missing in pairs
        ]

    return WhatCanICookOut(complete=pack(complete), missing_one=pack(missing_one))
