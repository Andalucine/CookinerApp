"""Pantry ("what do I have") and the shopping list, per notebook."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Notebook,
    PantryItem,
    Recipe,
    RecipeIngredient,
    ShoppingListItem,
    ShoppingSection,
    User,
)
from app.services.recipe import get_or_create_ingredient

# Things every kitchen has: never counted as missing.
STAPLES = {"sal", "agua", "aceite", "aceite de oliva", "pimienta negra", "azúcar"}


def list_items(db: Session, notebook_id: int) -> list[PantryItem]:
    return db.scalars(
        select(PantryItem)
        .options(selectinload(PantryItem.ingredient))
        .where(PantryItem.notebook_id == notebook_id)
        .order_by(PantryItem.location, PantryItem.id)
    ).all()


def add_item(db: Session, notebook_id: int, name: str, location: str | None) -> PantryItem:
    ingredient = get_or_create_ingredient(db, name)
    item = db.scalar(
        select(PantryItem).where(
            PantryItem.notebook_id == notebook_id, PantryItem.ingredient_id == ingredient.id
        )
    )
    if item is None:
        item = PantryItem(notebook_id=notebook_id, ingredient_id=ingredient.id, location=location)
        db.add(item)
    else:
        item.location = location
    db.commit()
    db.refresh(item)
    return item


def remove_item(db: Session, notebook_id: int, item_id: int) -> bool:
    item = db.get(PantryItem, item_id)
    if item is None or item.notebook_id != notebook_id:
        return False
    db.delete(item)
    db.commit()
    return True


def what_can_i_cook(db: Session, notebook_id: int) -> tuple[list, list]:
    """Returns (complete, missing_one): lists of (recipe, [missing ingredients])."""
    have = {p.ingredient_id for p in list_items(db, notebook_id)}
    recipes = db.scalars(
        select(Recipe)
        .options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
            selectinload(Recipe.categories),
            selectinload(Recipe.author),
            selectinload(Recipe.notebook),
        )
        .where(Recipe.notebook_id == notebook_id)
        .order_by(Recipe.title)
    ).all()
    complete, missing_one = [], []
    for recipe in recipes:
        needed = [ri.ingredient for ri in recipe.ingredients if ri.ingredient.name not in STAPLES]
        if not needed:
            continue
        missing = [i for i in needed if i.id not in have]
        if not missing:
            complete.append((recipe, []))
        elif len(missing) == 1:
            missing_one.append((recipe, missing))
    return complete, missing_one


# --- Shopping list -------------------------------------------------------------------------


def shopping_items(db: Session, notebook_id: int) -> list[ShoppingListItem]:
    return db.scalars(
        select(ShoppingListItem)
        .options(selectinload(ShoppingListItem.section))
        .where(ShoppingListItem.notebook_id == notebook_id)
        .order_by(ShoppingListItem.is_checked, ShoppingListItem.position, ShoppingListItem.id)
    ).all()


def _section_for(db: Session, ingredient) -> int | None:
    if ingredient is not None and ingredient.shopping_section_id is not None:
        return ingredient.shopping_section_id
    other = db.scalar(select(ShoppingSection).where(ShoppingSection.code == "other"))
    return other.id if other else None


def add_shopping_item(
    db: Session,
    notebook: Notebook,
    user: User,
    text: str,
    quantity: str | None = None,
    ingredient_name: str | None = None,
    recipe_id: int | None = None,
) -> ShoppingListItem:
    ingredient = get_or_create_ingredient(db, ingredient_name or text)
    item = ShoppingListItem(
        notebook_id=notebook.id,
        ingredient_id=ingredient.id,
        text=text.strip(),
        quantity=quantity,
        section_id=_section_for(db, ingredient),
        recipe_id=recipe_id,
        added_by_id=user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def add_missing_from_recipe(db: Session, notebook: Notebook, user: User, recipe: Recipe) -> list:
    """Put on the list every ingredient of the recipe that is not in the pantry."""
    have = {p.ingredient_id for p in list_items(db, notebook.id)}
    already = {
        i.ingredient_id
        for i in shopping_items(db, notebook.id)
        if not i.is_checked and i.ingredient_id
    }
    added = []
    for ri in recipe.ingredients:
        ing = ri.ingredient
        if ing.name in STAPLES or ing.id in have or ing.id in already:
            continue
        item = ShoppingListItem(
            notebook_id=notebook.id,
            ingredient_id=ing.id,
            text=ing.name,
            quantity=ri.raw_text,
            section_id=_section_for(db, ing),
            recipe_id=recipe.id,
            added_by_id=user.id,
        )
        db.add(item)
        added.append(item)
    db.commit()
    return added


def set_checked(db: Session, notebook_id: int, item_id: int, checked: bool) -> bool:
    item = db.get(ShoppingListItem, item_id)
    if item is None or item.notebook_id != notebook_id:
        return False
    item.is_checked = checked
    db.commit()
    return True


def remove_shopping_item(db: Session, notebook_id: int, item_id: int) -> bool:
    item = db.get(ShoppingListItem, item_id)
    if item is None or item.notebook_id != notebook_id:
        return False
    db.delete(item)
    db.commit()
    return True


def clear_checked(db: Session, notebook_id: int) -> int:
    items = [i for i in shopping_items(db, notebook_id) if i.is_checked]
    for item in items:
        db.delete(item)
    db.commit()
    return len(items)
