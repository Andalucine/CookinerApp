"""Menú semanal (session 9): a week of meals made only with the recipes of the notebook,
kept as its own entity so that the shopping list can read it (decision, session 8)."""

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.recipe import Recipe

MEALS = ("breakfast", "lunch", "dinner")
DAYS = 7  # Monday (0) to Sunday (6)


class WeeklyMenu(TimestampMixin, Base):
    __tablename__ = "weekly_menus"
    __table_args__ = (UniqueConstraint("notebook_id", "week_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)  # always a Monday
    meals: Mapped[str] = mapped_column(String(40), nullable=False)  # "breakfast,lunch,dinner"
    wants: Mapped[str | None] = mapped_column(String(300))  # "¿qué te apetece?": foods
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    slots: Mapped[list["MenuSlot"]] = relationship(
        back_populates="menu", cascade="all, delete-orphan", order_by="MenuSlot.id"
    )

    @property
    def meal_list(self) -> list[str]:
        return [m for m in self.meals.split(",") if m]


class MenuSlot(Base):
    """One meal of one day: a recipe of the notebook, a note written by hand, or empty."""

    __tablename__ = "menu_slots"
    __table_args__ = (UniqueConstraint("menu_id", "day", "meal"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    menu_id: Mapped[int] = mapped_column(
        ForeignKey("weekly_menus.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 = Monday
    meal: Mapped[str] = mapped_column(String(10), nullable=False)  # one of MEALS
    recipe_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id", ondelete="SET NULL"))
    note: Mapped[str | None] = mapped_column(String(200))  # "sobras", "cenamos fuera"…

    menu: Mapped[WeeklyMenu] = relationship(back_populates="slots")
    recipe: Mapped[Recipe | None] = relationship()
