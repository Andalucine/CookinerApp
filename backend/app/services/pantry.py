"""Pantry ("what do I have") and the shopping list, per notebook."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Notebook,
    NotebookIngredientSection,
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


def set_item_photo(db: Session, notebook_id: int, item_id: int, url: str | None):
    item = db.get(PantryItem, item_id)
    if item is None or item.notebook_id != notebook_id:
        return None
    item.image_url = url
    db.commit()
    db.refresh(item)
    return item


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


def _section_for(db: Session, ingredient, notebook_id: int | None = None) -> int | None:
    """The notebook's own choice first (session 9), then the catalogue, then "Otros"."""
    if ingredient is not None and notebook_id is not None:
        own = db.scalar(
            select(NotebookIngredientSection.section_id).where(
                NotebookIngredientSection.notebook_id == notebook_id,
                NotebookIngredientSection.ingredient_id == ingredient.id,
            )
        )
        if own is not None:
            return own
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
        section_id=_section_for(db, ingredient, notebook.id),
        recipe_id=recipe_id,
        added_by_id=user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def missing_from_recipes(db: Session, notebook_id: int, recipes: list[Recipe]) -> list[dict]:
    """What each ingredient of those recipes is, before adding anything (session 9): `missing`
    (would go to the list), `in_pantry`, `pending` (already on the list) or `staple`. One
    line per ingredient, even if several recipes use it; `quantity` joins what they say."""
    have = {p.ingredient_id for p in list_items(db, notebook_id)}
    already = {
        i.ingredient_id
        for i in shopping_items(db, notebook_id)
        if not i.is_checked and i.ingredient_id
    }
    rows: dict[int, dict] = {}
    for recipe in recipes:
        for ri in recipe.ingredients:
            ing = ri.ingredient
            row = rows.setdefault(
                ing.id,
                {
                    "ingredient_id": ing.id,
                    "name": ing.name,
                    "quantity": None,
                    "recipes": [],
                    "status": "missing",
                },
            )
            if ri.raw_text and ri.raw_text not in (row["quantity"] or ""):
                row["quantity"] = (
                    f"{row['quantity']} · {ri.raw_text}" if row["quantity"] else ri.raw_text
                )
            if recipe.title not in row["recipes"]:
                row["recipes"].append(recipe.title)
            if ing.name in STAPLES:
                row["status"] = "staple"
            elif ing.id in have:
                row["status"] = "in_pantry"
            elif ing.id in already:
                row["status"] = "pending"
    return list(rows.values())


def add_missing_from_recipe(
    db: Session,
    notebook: Notebook,
    user: User,
    recipe: Recipe,
    ingredient_ids: list[int] | None = None,
) -> list:
    """Put on the list every ingredient of the recipe that is not in the pantry, or, when
    `ingredient_ids` is given (session 9), exactly those the person ticked (even if they are
    in the pantry), skipping only what is already pending."""
    have = {p.ingredient_id for p in list_items(db, notebook.id)}
    already = {
        i.ingredient_id
        for i in shopping_items(db, notebook.id)
        if not i.is_checked and i.ingredient_id
    }
    added = []
    for ri in recipe.ingredients:
        ing = ri.ingredient
        if ing.id in already:
            continue
        if ingredient_ids is not None:
            if ing.id not in ingredient_ids:
                continue
        elif ing.name in STAPLES or ing.id in have:
            continue
        already.add(ing.id)
        item = ShoppingListItem(
            notebook_id=notebook.id,
            ingredient_id=ing.id,
            text=ing.name,
            quantity=ri.raw_text,
            section_id=_section_for(db, ing, notebook.id),
            recipe_id=recipe.id,
            added_by_id=user.id,
        )
        db.add(item)
        added.append(item)
    db.commit()
    return added


def shopping_item(db: Session, notebook_id: int, item_id: int) -> ShoppingListItem | None:
    item = db.get(ShoppingListItem, item_id)
    return item if item is not None and item.notebook_id == notebook_id else None


def set_shopping_photo(db: Session, notebook_id: int, item_id: int, url: str | None):
    item = shopping_item(db, notebook_id, item_id)
    if item is None:
        return None
    item.image_url = url
    db.commit()
    db.refresh(item)
    return item


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


def move_item(db: Session, notebook_id: int, item_id: int, section_code: str):
    """Put a line in another section. The notebook remembers it for that ingredient, and the
    other pending lines of the same ingredient move too. None if the item or section is not
    found."""
    item = db.get(ShoppingListItem, item_id)
    section = db.scalar(select(ShoppingSection).where(ShoppingSection.code == section_code))
    if item is None or item.notebook_id != notebook_id or section is None:
        return None
    item.section_id = section.id
    if item.ingredient_id is not None:
        own = db.scalar(
            select(NotebookIngredientSection).where(
                NotebookIngredientSection.notebook_id == notebook_id,
                NotebookIngredientSection.ingredient_id == item.ingredient_id,
            )
        )
        if own is None:
            db.add(
                NotebookIngredientSection(
                    notebook_id=notebook_id,
                    ingredient_id=item.ingredient_id,
                    section_id=section.id,
                )
            )
        else:
            own.section_id = section.id
        for other in shopping_items(db, notebook_id):
            if other.ingredient_id == item.ingredient_id and not other.is_checked:
                other.section_id = section.id
    db.commit()
    db.refresh(item)
    return item


# Where what was bought is kept at home, by its supermarket section (session 9)
_LOCATION_BY_SECTION = {
    "frozen": "freezer",
    "produce": "fridge",
    "meat": "fridge",
    "fish": "fridge",
    "dairy": "fridge",
}


def clear_checked(db: Session, notebook_id: int, to_pantry: bool = False) -> tuple[int, int]:
    """Remove what was already bought. With `to_pantry`, each bought ingredient is noted in
    the pantry first (fridge, freezer or pantry by its section). Returns (removed, noted)."""
    items = [i for i in shopping_items(db, notebook_id) if i.is_checked]
    noted = 0
    if to_pantry:
        have = {p.ingredient_id for p in list_items(db, notebook_id)}
        for item in items:
            if item.ingredient_id is None or item.ingredient_id in have:
                continue
            code = item.section.code if item.section else None
            db.add(
                PantryItem(
                    notebook_id=notebook_id,
                    ingredient_id=item.ingredient_id,
                    location=_LOCATION_BY_SECTION.get(code, "pantry"),
                )
            )
            have.add(item.ingredient_id)
            noted += 1
    for item in items:
        db.delete(item)
    db.commit()
    return len(items), noted
