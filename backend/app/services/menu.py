"""Menú semanal (session 9): a draft for the week made with the recipes of the notebook and
plain rules, no artificial intelligence (decision, session 8), so that the result is
predictable. The person then changes any plate."""

import random
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
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


def _in_season(recipe: Recipe, season: str) -> bool:
    return not recipe.seasons or any(s.code == season for s in recipe.seasons)


def _primary_category_id(recipe: Recipe) -> int | None:
    for rc in recipe.categories:
        if rc.is_primary:
            return rc.category_id
    return recipe.categories[0].category_id if recipe.categories else None


def _wanted(recipe: Recipe, foods: list[str]) -> bool:
    if not foods:
        return False
    names = [ri.ingredient.name.lower() for ri in recipe.ingredients] + [recipe.title.lower()]
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
    main: list[Recipe]
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


def _pools(recipes: list[Recipe], season: str) -> _Pools:
    pools = _Pools(
        breakfast=[r for r in recipes if _is_breakfast(r)],
        main=[r for r in recipes if not _is_breakfast(r)],
    )
    # The season of the week applies, unless it would leave nothing to choose from
    for name in ("breakfast", "main"):
        pool = getattr(pools, name)
        seasonal = [r for r in pool if _in_season(r, season)]
        if seasonal:
            setattr(pools, name, seasonal)
        elif pool:
            pools.notices.append("season_ignored")
    return pools


class _Picker:
    """Chooses a recipe for each meal, in order, with the rules of the bible: no repeats
    while there are recipes left, the wanted foods first, what the pantry allows first, and
    not two plates of the same category in a row."""

    def __init__(self, foods: list[str], have: set[int], seed: str):
        self.foods = foods
        self.have = have
        self.random = random.Random(seed)
        self.used: dict[int, int] = {}
        self.last_category: int | None = None
        self.filled_with_rest = False

    def pick(
        self, pool: list[Recipe], avoid: set[int] = frozenset(), never: set[int] = frozenset()
    ) -> Recipe | None:
        """`avoid` when possible (the rest of the week); `never` unless nothing else is left
        (the recipe being replaced)."""
        candidates = (
            [r for r in pool if r.id not in avoid and r.id not in never]
            or [r for r in pool if r.id not in never]
            or list(pool)
        )
        if not candidates:
            return None
        self.random.shuffle(candidates)  # ties in a different order every week
        least_used = min(self.used.get(r.id, 0) for r in candidates)

        def score(r: Recipe) -> tuple:
            return (
                self.used.get(r.id, 0) == least_used,  # never repeat while others are unused
                _wanted(r, self.foods),
                _primary_category_id(r) != self.last_category,
                _pantry_score(r, self.have),
            )

        chosen = max(candidates, key=score)
        if self.foods and not _wanted(chosen, self.foods):
            self.filled_with_rest = True
        self.used[chosen.id] = self.used.get(chosen.id, 0) + 1
        self.last_category = _primary_category_id(chosen)
        return chosen


def draft(db: Session, notebook: Notebook, user: User, week_start: date, meals: list[str],
          wants: str | None) -> WeeklyMenu:  # fmt: skip
    """Make (or remake) the menu of that week. Replaces the previous one of the same week."""
    monday = monday_of(week_start)
    season = season_for(monday)
    foods = parse_wants(wants)
    pools = _pools(_recipes(db, notebook.id), season)
    have = {p.ingredient_id for p in pantry_service.list_items(db, notebook.id)}
    picker = _Picker(foods, have, f"{notebook.id}-{monday.isoformat()}")

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
    for day in range(DAYS):
        picker.last_category = None  # a new day starts fresh
        for meal in menu.meal_list:
            pool = pools.breakfast if meal == "breakfast" else pools.main
            chosen = picker.pick(pool)
            db.add(
                MenuSlot(
                    menu_id=menu.id, day=day, meal=meal, recipe_id=chosen.id if chosen else None
                )
            )
    if picker.filled_with_rest:
        notices.append("filled_with_rest")
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
    pools = _pools(_recipes(db, menu.notebook_id), season)
    pool = pools.breakfast if slot.meal == "breakfast" else pools.main
    have = {p.ingredient_id for p in pantry_service.list_items(db, menu.notebook_id)}
    picker = _Picker(parse_wants(menu.wants), have, f"{menu.id}-{slot.id}-{random.random()}")
    in_week = {s.recipe_id for s in menu.slots if s.recipe_id is not None}
    same_day = [s for s in menu.slots if s.day == slot.day and s.id != slot.id and s.recipe]
    if same_day:
        picker.last_category = _primary_category_id(same_day[-1].recipe)
    chosen = picker.pick(pool, avoid=in_week, never={slot.recipe_id or 0})
    slot.recipe_id = chosen.id if chosen else None
    slot.note = None
    db.commit()
    db.expire(menu)
    return slot_of(get(db, menu.id), slot.id)


def shopping_for_week(db: Session, menu: WeeklyMenu, notebook: Notebook, user: User) -> tuple:
    """ "Añadir lo que falta para toda la semana": every ingredient of the week's recipes that
    is not in the pantry nor already pending. Returns (items added, recipes looked at)."""
    added, seen = [], set()
    for slot in menu.slots:
        if slot.recipe is None or slot.recipe_id in seen:
            continue
        seen.add(slot.recipe_id)
        added.extend(pantry_service.add_missing_from_recipe(db, notebook, user, slot.recipe))
    return added, len(seen)


def delete(db: Session, menu: WeeklyMenu) -> None:
    db.delete(menu)
    db.commit()
