"""Lista de la compra of the user's notebook, grouped by supermarket section."""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.models import ShoppingSection
from app.schemas.auth import MessageResponse
from app.schemas.pantry import (
    ShoppingItemIn,
    ShoppingItemOut,
    ShoppingItemPatch,
    ShoppingListOut,
    ShoppingSectionGroup,
)
from app.services import pantry as pantry_service
from app.services import permissions
from app.services import recipe as recipe_service

router = APIRouter(prefix="/shopping-list", tags=["shopping-list"])


@router.get("", response_model=ShoppingListOut)
def get_shopping_list(db: DbSession, user: CurrentUser) -> ShoppingListOut:
    items = pantry_service.shopping_items(db, user.notebook.id)
    sections = db.scalars(select(ShoppingSection).order_by(ShoppingSection.position)).all()
    groups = []
    for s in sections:
        mine = [ShoppingItemOut.model_validate(i) for i in items if i.section_id == s.id]
        if mine:
            groups.append(
                ShoppingSectionGroup(
                    section_id=s.id, code=s.code, name_es=s.name_es, name_en=s.name_en, items=mine
                )
            )
    orphans = [ShoppingItemOut.model_validate(i) for i in items if i.section_id is None]
    if orphans:
        groups.append(
            ShoppingSectionGroup(
                section_id=None, code="other", name_es="Otros", name_en="Other", items=orphans
            )  # fmt: skip
        )
    return ShoppingListOut(
        sections=groups, total=len(items), pending=sum(1 for i in items if not i.is_checked)
    )


@router.post("/items", response_model=ShoppingItemOut, status_code=status.HTTP_201_CREATED)
def add_item(body: ShoppingItemIn, db: DbSession, user: CurrentUser) -> ShoppingItemOut:
    """Write something by hand; it lands in the section of the matching ingredient."""
    item = pantry_service.add_shopping_item(
        db, user.notebook, user, body.text, body.quantity, body.ingredient_name
    )
    return ShoppingItemOut.model_validate(item)


@router.post("/from-recipe/{recipe_id}", response_model=list[ShoppingItemOut])
def add_missing_from_recipe(
    recipe_id: int, db: DbSession, user: CurrentUser, lang: Lang
) -> list[ShoppingItemOut]:
    """'Añadir lo que me falta': every ingredient of the recipe not in my pantry."""
    try:
        recipe = recipe_service.get(db, recipe_id)
        permissions.require_view(db, user, recipe.notebook)
    except (recipe_service.RecipeNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("recipe_not_found", lang)) from None
    added = pantry_service.add_missing_from_recipe(db, user.notebook, user, recipe)
    return [ShoppingItemOut.model_validate(i) for i in added]


@router.post("/items/{item_id}/check", response_model=MessageResponse)
def check_item(item_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    if not pantry_service.set_checked(db, user.notebook.id, item_id, True):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang))
    return MessageResponse(message=t("ok", lang))


@router.post("/items/{item_id}/uncheck", response_model=MessageResponse)
def uncheck_item(item_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    if not pantry_service.set_checked(db, user.notebook.id, item_id, False):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang))
    return MessageResponse(message=t("ok", lang))


@router.patch("/items/{item_id}", response_model=ShoppingItemOut)
def patch_item(
    item_id: int, body: ShoppingItemPatch, db: DbSession, user: CurrentUser, lang: Lang
) -> ShoppingItemOut:
    """Put a line in another section (the notebook remembers it for that ingredient) and/or
    set its photo."""
    sent = body.model_dump(exclude_unset=True)
    item = None
    if "section_code" in sent and body.section_code:
        item = pantry_service.move_item(db, user.notebook.id, item_id, body.section_code)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang))
    if "image_url" in sent:
        item = pantry_service.set_shopping_photo(db, user.notebook.id, item_id, body.image_url)
    if item is None:
        item = pantry_service.shopping_item(db, user.notebook.id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang))
    return ShoppingItemOut.model_validate(item)


@router.delete("/items/{item_id}", response_model=MessageResponse)
def remove_item(item_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    if not pantry_service.remove_shopping_item(db, user.notebook.id, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang))
    return MessageResponse(message=t("ok", lang))


@router.delete("/checked", response_model=MessageResponse)
def clear_checked(
    db: DbSession,
    user: CurrentUser,
    lang: Lang,
    to_pantry: bool = Query(default=False, description="Note what was bought in the pantry"),
) -> MessageResponse:
    """Remove everything already bought (and, if asked, note it in the pantry first)."""
    n, noted = pantry_service.clear_checked(db, user.notebook.id, to_pantry)
    if to_pantry:
        return MessageResponse(message=t("shopping_cleared_pantry", lang).format(n=n, m=noted))
    return MessageResponse(message=t("shopping_cleared", lang).format(n=n))
