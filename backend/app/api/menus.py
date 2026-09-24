"""Menú semanal (session 9): the week's meals, made from the notebook's own recipes. Always
the person's own notebook, like the pantry and the shopping list."""

from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.models import MenuSlot, WeeklyMenu
from app.schemas.auth import MessageResponse
from app.schemas.menu import MenuCheckOut, MenuDraftIn, MenuOut, MenuShoppingOut, SlotIn, SlotOut
from app.schemas.pantry import AddMissingIn, MissingIngredientOut, ShoppingItemOut
from app.services import menu as menu_service
from app.services import pantry as pantry_service
from app.services import recipe as recipe_service

router = APIRouter(prefix="/menus", tags=["menus"])


def _slot_out(slot: MenuSlot, favorites: set[int]) -> SlotOut:
    from app.api.recipes import to_summary

    return SlotOut(
        id=slot.id,
        day=slot.day,
        meal=slot.meal,
        recipe=to_summary(slot.recipe, favorites) if slot.recipe else None,
        note=slot.note,
    )


def _out(db, user, menu: WeeklyMenu, notices: list[str] | None = None) -> MenuOut:
    ids = [s.recipe_id for s in menu.slots if s.recipe_id]
    favorites = recipe_service.favorite_ids(db, user.id, ids)
    return MenuOut(
        id=menu.id,
        week_start=menu.week_start,
        meals=menu.meal_list,
        wants=menu.wants,
        slots=[_slot_out(s, favorites) for s in menu.slots],
        notices=notices or [],
    )


def _mine(db, user, lang, menu_id: int) -> WeeklyMenu:
    try:
        menu = menu_service.get(db, menu_id)
    except menu_service.MenuNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang)) from None
    if menu.notebook_id != user.notebook.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang))
    return menu


@router.get("/check", response_model=MenuCheckOut)
def check(db: DbSession, user: CurrentUser, week_start: date = Query()) -> MenuCheckOut:
    """Before a draft: how many recipes there are for breakfast and for the rest."""
    return MenuCheckOut(**menu_service.check(db, user.notebook.id, week_start))


@router.get("", response_model=MenuOut)
def get_menu(db: DbSession, user: CurrentUser, lang: Lang, week_start: date = Query()) -> MenuOut:
    """The menu of the week that contains that date, or 404 if there is none yet."""
    menu = menu_service.get_for_week(db, user.notebook.id, week_start)
    if menu is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang))
    return _out(db, user, menu)


@router.post("/draft", response_model=MenuOut, status_code=status.HTTP_201_CREATED)
def make_draft(body: MenuDraftIn, db: DbSession, user: CurrentUser) -> MenuOut:
    """A draft for the week (replaces the one of that week, if any), with `notices`."""
    menu, notices = menu_service.draft(
        db, user.notebook, user, body.week_start, list(body.meals), body.wants
    )
    return _out(db, user, menu, notices)


@router.put("/{menu_id}/slots/{slot_id}", response_model=SlotOut)
def set_slot(
    menu_id: int, slot_id: int, body: SlotIn, db: DbSession, user: CurrentUser, lang: Lang
) -> SlotOut:
    """Choose a recipe of the notebook for that meal, write it by hand, or leave it empty."""
    menu = _mine(db, user, lang, menu_id)
    try:
        slot = menu_service.set_slot(
            db, menu, menu_service.slot_of(menu, slot_id), body.recipe_id, body.note
        )
    except menu_service.SlotNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang)) from None
    favorites = recipe_service.favorite_ids(db, user.id, [slot.recipe_id] if slot.recipe_id else [])
    return _slot_out(slot, favorites)


@router.post("/{menu_id}/slots/{slot_id}/another", response_model=SlotOut)
def another(menu_id: int, slot_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> SlotOut:
    """ "Otra propuesta" for that meal."""
    menu = _mine(db, user, lang, menu_id)
    try:
        slot = menu_service.another(db, menu, menu_service.slot_of(menu, slot_id))
    except menu_service.SlotNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang)) from None
    favorites = recipe_service.favorite_ids(db, user.id, [slot.recipe_id] if slot.recipe_id else [])
    return _slot_out(slot, favorites)


@router.get("/{menu_id}/shopping", response_model=list[MissingIngredientOut])
def shopping_preview(
    menu_id: int, db: DbSession, user: CurrentUser, lang: Lang
) -> list[MissingIngredientOut]:
    """Before adding: every ingredient of the week's recipes, once, with what it is for me."""
    menu = _mine(db, user, lang, menu_id)
    rows = pantry_service.missing_from_recipes(
        db, user.notebook.id, menu_service.recipes_of_week(menu)
    )
    return [MissingIngredientOut(**r) for r in rows]


@router.post("/{menu_id}/shopping", response_model=MenuShoppingOut)
def shopping(
    menu_id: int, db: DbSession, user: CurrentUser, lang: Lang, body: AddMissingIn | None = None
) -> MenuShoppingOut:
    """ "Añadir lo que falta para toda la semana" to my shopping list (or the ticked ones)."""
    menu = _mine(db, user, lang, menu_id)
    added, recipes = menu_service.shopping_for_week(
        db, menu, user.notebook, user, body.ingredient_ids if body else None
    )
    return MenuShoppingOut(
        added=[ShoppingItemOut.model_validate(i) for i in added], recipes=recipes
    )


@router.delete("/{menu_id}", response_model=MessageResponse)
def delete_menu(menu_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    menu_service.delete(db, _mine(db, user, lang, menu_id))
    return MessageResponse(message=t("ok", lang))
