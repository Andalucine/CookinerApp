"""Menú semanal (session 9): a draft for the week made with the recipes of the notebook and
plain rules, no artificial intelligence (decision, session 8), so that the result is
predictable. The person then changes any plate."""

import random
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Category,
    MenuSlot,
    Notebook,
    Recipe,
    RecipeCategory,
    RecipeIngredient,
    User,
    WeeklyMenu,
)
from app.models.menu import DAYS, MEALS
from app.services import pantry as pantry_service
from app.services.pantry import STAPLES

BREAKFAST_TAG = ("course", "breakfast")
# Course tags that are never a lunch or a dinner on their own (session 9, after Beatriz's test)
_NOT_A_MAIN_COURSE = {"dessert", "appetiser", "snack"}
# Second-level categories whose recipes are not a main plate either
_NOT_A_MAIN_CATEGORY = {"aperitivos-tapas", "salsas-alinos-basicos"}
_NOT_A_MAIN_SLUG = {"pan", "caldos-fondos", "guarniciones", "encurtidos-conservas"}
# What makes a light dinner, and what is a hearty lunch (a preference, not a rule)
_LIGHT_CATEGORIES = {
    "ensaladas",
    "sopas-cremas-caldos",
    "huevos",
    "verduras-hortalizas",
    "pescados",
}
_HEARTY_CATEGORIES = {"guisos-cuchara", "legumbres", "carnes", "arroces-cereales", "pasta-fideos"}
MAX_USES_PER_WEEK = 2  # a lunch/dinner may repeat once in the week; then the plate stays empty


class MenuNotFound(Exception):
    pass


class SlotNotFound(Exception):
    pass


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def season_for(day: date) -> str:
    """The season of a date in Spain (astronomical, rounded to the 21st)."""
    m, d = day.month, day.day
    if (m == 3 and d >= 21) or m in (4, 5) or (m == 6 and d < 21):
        return "spring"
    if (m == 6 and d >= 21) or m in (7, 8) or (m == 9 and d < 21):
        return "summer"
    if (m == 9 and d >= 21) or m in (10, 11) or (m == 12 and d < 21):
        return "autumn"
    return "winter"


def _recipes(db: Session, notebook_id: int) -> list[Recipe]:
    return list(
        db.scalars(
            select(Recipe)
            .options(
                selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
                selectinload(Recipe.categories).selectinload(RecipeCategory.category),
                selectinload(Recipe.tags),
                selectinload(Recipe.seasons),
                selectinload(Recipe.author),
                selectinload(Recipe.notebook),
            )
            .where(Recipe.notebook_id == notebook_id)
            .order_by(Recipe.id)
        )
    )


def _is_breakfast(recipe: Recipe) -> bool:
    return any((t.kind, t.code) == BREAKFAST_TAG for t in recipe.tags)


def _course_codes(recipe: Recipe) -> set[str]:
    return {t.code for t in recipe.tags if t.kind == "course"}


class _Tree:
    """The category tree as id → (parent id, slug), to know the branch of a recipe."""

    def __init__(self, db: Session):
        self.parent: dict[int, int | None] = {}
        self.slug: dict[int, str] = {}
        for cat in db.scalars(select(Category)):
            self.parent[cat.id] = cat.parent_id
            self.slug[cat.id] = cat.slug

    def chain(self, category_id: int | None) -> list[str]:
        """Slugs from the recipe's category up to the root: ["guisos-legumbres", "legumbres",
        "salado"]."""
        out: list[str] = []
        seen: set[int] = set()
        while category_id is not None and category_id not in seen:
            seen.add(category_id)
            out.append(self.slug.get(category_id, ""))
            category_id = self.parent.get(category_id)
        return out

    def branch(self, recipe: Recipe) -> list[str]:
        return self.chain(_primary_category_id(recipe))

    def is_main_plate(self, recipe: Recipe) -> bool:
        """A lunch or a dinner on its own: savoury, not a tapa, a sauce, a bread, a stock or a
        side, and not tagged dessert, appetiser or snack (session 9)."""
        chain = self.branch(recipe)
        if chain and chain[-1] != "salado":
            return False  # sweets and drinks
        if set(chain) & (_NOT_A_MAIN_CATEGORY | _NOT_A_MAIN_SLUG):
            return False
        return not (_course_codes(recipe) & _NOT_A_MAIN_COURSE)

    def is_light(self, recipe: Recipe) -> bool:
        """Good for a dinner: tagged "cena ligera", a salad, a soup, eggs, vegetables, fish,
        or quick to make."""
        codes = _course_codes(recipe)
        if "light-dinner" in codes:
            return True
        if "main" in codes and (recipe.prep_time_minutes or 0) > 45:
            return False
        if set(self.branch(recipe)) & _LIGHT_CATEGORIES:
            return True
        return (recipe.prep_time_minutes or 999) <= 30

    def is_hearty(self, recipe: Recipe) -> bool:
        return bool(set(self.branch(recipe)) & _HEARTY_CATEGORIES)


def _in_season(recipe: Recipe, season: str) -> bool:
    return not recipe.seasons or any(s.code == season for s in recipe.seasons)


def _primary_category_id(recipe: Recipe) -> int | None:
    for rc in recipe.categories:
        if rc.is_primary:
            return rc.category_id
    return recipe.categories[0].category_id if recipe.categories else None


def _wanted(recipe: Recipe, foods: list[str]) -> bool:
    """ "pollo", "verduras", "cerdo"…: in an ingredient, in the title or in the name of one of
    its categories (so "verduras" finds "Verduras y hortalizas")."""
    if not foods:
        return False
    names = (
        [ri.ingredient.name.lower() for ri in recipe.ingredients]
        + [recipe.title.lower()]
        + [rc.category.name_es.lower() for rc in recipe.categories]
    )
    return any(any(food in name for name in names) for food in foods)


def _pantry_score(recipe: Recipe, have: set[int]) -> float:
    needed = [ri.ingredient_id for ri in recipe.ingredients if ri.ingredient.name not in STAPLES]
    if not needed:
        return 0.0
    return sum(1 for i in needed if i in have) / len(needed)


def parse_wants(text: str | None) -> list[str]:
    return [w.strip().lower() for w in (text or "").replace(";", ",").split(",") if w.strip()]


@dataclass
class _Pools:
    breakfast: list[Recipe]
    main: list[Recipe]  # only main plates (session 9)
    season: str
    tree: _Tree
    notices: list[str] = field(default_factory=list)


def check(db: Session, notebook_id: int, week_start: date) -> dict:
    recipes = _recipes(db, notebook_id)
    breakfast = sum(1 for r in recipes if _is_breakfast(r))
    return {
        "week_start": monday_of(week_start),
        "season": season_for(monday_of(week_start)),
        "total_recipes": len(recipes),
        "breakfast_recipes": breakfast,
        "main_recipes": len(recipes) - breakfast,
    }


def _pools(db: Session, recipes: list[Recipe], season: str) -> _Pools:
    """Breakfasts are the recipes tagged breakfast; lunches and dinners come only from the
    main plates (no desserts, tapas, sauces, breads…). The season is a preference of the
    picker, not a filter: with a small notebook, a recipe of another season is better than
    the same plate every day (session 9)."""
    tree = _Tree(db)
    return _Pools(
        breakfast=[r for r in recipes if _is_breakfast(r)],
        main=[r for r in recipes if not _is_breakfast(r) and tree.is_main_plate(r)],
        season=season,
        tree=tree,
    )


class _Picker:
    """Chooses a recipe for each meal, in order, with the rules of the bible: no repeats
    while there are recipes left, the wanted foods first, what the pantry allows first, and
    not two plates of the same category in a row."""

    def __init__(self, foods: list[str], have: set[int], season: str, tree: _Tree, seed: str):
        self.foods = foods
        self.have = have
        self.season = season
        self.tree = tree
        self.random = random.Random(seed)
        self.used: dict[int, int] = {}
        self.last_category: int | None = None
        self.filled_with_rest = False
        self.out_of_season = False
        self.left_empty = False

    def _fits(self, recipe: Recipe, meal: str) -> bool:
        """A light plate at dinner, a hearty one at lunch (preference, session 9)."""
        if meal == "dinner":
            return self.tree.is_light(recipe)
        if meal == "lunch":
            return self.tree.is_hearty(recipe) or not self.tree.is_light(recipe)
        return True

    def pick(
        self,
        pool: list[Recipe],
        meal: str,
        avoid: set[int] = frozenset(),
        never: set[int] = frozenset(),
    ) -> Recipe | None:
        """`avoid` when possible (the rest of the week); `never` unless nothing else is left
        (the recipe being replaced). A recipe is used at most MAX_USES_PER_WEEK times: past
        that, the plate stays empty rather than repeating (session 9)."""
        # Breakfasts may repeat every day (toast is toast); lunches and dinners are capped
        fresh = [
            r for r in pool if meal == "breakfast" or self.used.get(r.id, 0) < MAX_USES_PER_WEEK
        ]
        candidates = (
            [r for r in fresh if r.id not in avoid and r.id not in never]
            or [r for r in fresh if r.id not in never]
            or list(fresh)
        )
        if not candidates:
            if pool:
                self.left_empty = True
            return None
        self.random.shuffle(candidates)  # ties in a different order every week

        def score(r: Recipe) -> tuple:
            return (
                -self.used.get(r.id, 0),  # never repeat while others are unused
                _wanted(r, self.foods),
                self._fits(r, meal),
                _in_season(r, self.season),
                _primary_category_id(r) != self.last_category,
                _pantry_score(r, self.have),
            )

        chosen = max(candidates, key=score)
        if self.foods and not _wanted(chosen, self.foods):
            self.filled_with_rest = True
        if not _in_season(chosen, self.season):
            self.out_of_season = True
        self.used[chosen.id] = self.used.get(chosen.id, 0) + 1
        self.last_category = _primary_category_id(chosen)
        return chosen


def draft(db: Session, notebook: Notebook, user: User, week_start: date, meals: list[str],
          wants: str | None) -> WeeklyMenu:  # fmt: skip
    """Make (or remake) the menu of that week. Replaces the previous one of the same week."""
    monday = monday_of(week_start)
    season = season_for(monday)
    foods = parse_wants(wants)
    pools = _pools(db, _recipes(db, notebook.id), season)
    have = {p.ingredient_id for p in pantry_service.list_items(db, notebook.id)}
    picker = _Picker(foods, have, season, pools.tree, f"{notebook.id}-{monday.isoformat()}")

    existing = get_for_week(db, notebook.id, monday)
    if existing is not None:
        db.delete(existing)
        db.flush()
    menu = WeeklyMenu(
        notebook_id=notebook.id,
        week_start=monday,
        meals=",".join(m for m in MEALS if m in meals),
        wants=wants.strip() if wants and wants.strip() else None,
        created_by_id=user.id,
    )
    db.add(menu)
    db.flush()
    notices = list(pools.notices)
    if "breakfast" in meals and not pools.breakfast:
        notices.append("no_breakfast_recipes")
    if not pools.main and any(m != "breakfast" for m in menu.meal_list):
        notices.append("no_main_recipes")
    for day in range(DAYS):
        picker.last_category = None  # a new day starts fresh
        for meal in menu.meal_list:
            pool = pools.breakfast if meal == "breakfast" else pools.main
            chosen = picker.pick(pool, meal)
            db.add(
                MenuSlot(
                    menu_id=menu.id, day=day, meal=meal, recipe_id=chosen.id if chosen else None
                )
            )
    if picker.filled_with_rest:
        notices.append("filled_with_rest")
    if picker.out_of_season:
        notices.append("season_ignored")
    if picker.left_empty:
        notices.append("not_enough_recipes")
    main_slots = DAYS * sum(1 for m in menu.meal_list if m != "breakfast")
    if pools.main and main_slots > len(pools.main):
        notices.append("repeated")
    db.commit()
    return get(db, menu.id), notices


def _query():
    return select(WeeklyMenu).options(
        selectinload(WeeklyMenu.slots)
        .selectinload(MenuSlot.recipe)
        .options(
            selectinload(Recipe.categories).selectinload(RecipeCategory.category),
            selectinload(Recipe.author),
            selectinload(Recipe.notebook),
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
        )
    )


def get(db: Session, menu_id: int) -> WeeklyMenu:
    menu = db.scalar(_query().where(WeeklyMenu.id == menu_id))
    if menu is None:
        raise MenuNotFound
    return menu


def get_for_week(db: Session, notebook_id: int, week_start: date) -> WeeklyMenu | None:
    return db.scalar(
        _query().where(
            WeeklyMenu.notebook_id == notebook_id, WeeklyMenu.week_start == monday_of(week_start)
        )
    )


def slot_of(menu: WeeklyMenu, slot_id: int) -> MenuSlot:
    for slot in menu.slots:
        if slot.id == slot_id:
            return slot
    raise SlotNotFound


def set_slot(db: Session, menu: WeeklyMenu, slot: MenuSlot, recipe_id: int | None,
             note: str | None) -> MenuSlot:  # fmt: skip
    """The person chooses a recipe, writes something by hand, or leaves it empty."""
    if recipe_id is not None:
        recipe = db.get(Recipe, recipe_id)
        if recipe is None or recipe.notebook_id != menu.notebook_id:
            raise SlotNotFound
    slot.recipe_id = recipe_id
    slot.note = note.strip() if note and note.strip() else None
    db.commit()
    db.expire(menu)
    return slot_of(get(db, menu.id), slot.id)


def another(db: Session, menu: WeeklyMenu, slot: MenuSlot) -> MenuSlot:
    """ "Otra propuesta": a different recipe for that meal, avoiding the ones already in the
    week when there are enough."""
    season = season_for(menu.week_start)
    pools = _pools(db, _recipes(db, menu.notebook_id), season)
    pool = pools.breakfast if slot.meal == "breakfast" else pools.main
    have = {p.ingredient_id for p in pantry_service.list_items(db, menu.notebook_id)}
    picker = _Picker(
        parse_wants(menu.wants),
        have,
        season,
        pools.tree,
        f"{menu.id}-{slot.id}-{random.random()}",
    )
    for s in menu.slots:  # what the week already uses counts, so the cap holds here too
        if s.recipe_id is not None and s.id != slot.id:
            picker.used[s.recipe_id] = picker.used.get(s.recipe_id, 0) + 1
    in_week = {s.recipe_id for s in menu.slots if s.recipe_id is not None}
    same_day = [s for s in menu.slots if s.day == slot.day and s.id != slot.id and s.recipe]
    if same_day:
        picker.last_category = _primary_category_id(same_day[-1].recipe)
    chosen = picker.pick(pool, slot.meal, avoid=in_week, never={slot.recipe_id or 0})
    slot.recipe_id = chosen.id if chosen else None
    slot.note = None
    db.commit()
    db.expire(menu)
    return slot_of(get(db, menu.id), slot.id)


def recipes_of_week(menu: WeeklyMenu) -> list[Recipe]:
    seen, recipes = set(), []
    for slot in menu.slots:
        if slot.recipe is not None and slot.recipe_id not in seen:
            seen.add(slot.recipe_id)
            recipes.append(slot.recipe)
    return recipes


def shopping_for_week(
    db: Session,
    menu: WeeklyMenu,
    notebook: Notebook,
    user: User,
    ingredient_ids: list[int] | None = None,
) -> tuple:
    """ "Añadir lo que falta para toda la semana": every ingredient of the week's recipes that
    is not in the pantry nor already pending, or exactly the ticked ones (session 9).
    Returns (items added, recipes looked at)."""
    recipes = recipes_of_week(menu)
    added = []
    for recipe in recipes:
        added.extend(
            pantry_service.add_missing_from_recipe(db, notebook, user, recipe, ingredient_ids)
        )
    return added, len(recipes)


def delete(db: Session, menu: WeeklyMenu) -> None:
    db.delete(menu)
    db.commit()
