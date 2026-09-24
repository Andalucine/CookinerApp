"""Wines: type tree (global), the shop's wine catalogue (global, session 9: Vinoselección),
recommendations per recipe and the automatic pairing rules."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.user import User

if TYPE_CHECKING:
    from app.models.recipe import Recipe

# Facet codes stored in `wines` (labels for the app are in i18n: wine_sweetness.dry...).
# The seed script and the API both read them from here.
SWEETNESS = (
    "dry", "off_dry", "semi_sweet", "sweet",
    "brut_nature", "extra_brut", "brut", "extra_dry", "sec", "demi_sec", "doux",
)  # fmt: skip
BODY = ("light", "medium", "full")
AGEING = ("young", "oak", "crianza", "reserva", "gran_reserva", "solera")
PRICE_RANGES = ("€", "€€", "€€€", "€€€€")
# The bands each symbol stands for, in euros (session 8): €: < 15, €€: 15–30, €€€: 30–60, €€€€: > 60
PRICE_BAND_LIMITS = (15, 30, 60)


def price_range_for(price: float | None) -> str | None:
    if price is None:
        return None
    for symbol, limit in zip(PRICE_RANGES, PRICE_BAND_LIMITS, strict=False):
        if price < limit:
            return symbol
    return PRICE_RANGES[-1]


# The shop whose catalogue is the app's cellar (session 9: the app acts as its sales agent)
SHOP_VINOSELECCION = "vinoseleccion"
SHOP_NAMES = {SHOP_VINOSELECCION: "Vinoselección"}

ORIGIN_MANUAL = "manual"
ORIGIN_IMPORTED = "imported"


class WineCategory(Base):
    """Two-level tree: Tintos → Tinto joven, Tinto ligero y afrutado..."""

    __tablename__ = "wine_categories"
    __table_args__ = (UniqueConstraint("parent_id", "slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("wine_categories.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(String(60), nullable=False)
    name_es: Mapped[str] = mapped_column(String(80), nullable=False)
    name_en: Mapped[str] = mapped_column(String(80), nullable=False)
    name_fr: Mapped[str | None] = mapped_column(String(80))
    name_nl: Mapped[str | None] = mapped_column(String(80))
    name_de: Mapped[str | None] = mapped_column(String(80))
    examples_es: Mapped[str | None] = mapped_column(String(200))
    # Serving temperature range for the ficha, e.g. "6–8 °C"
    serving_temp: Mapped[str | None] = mapped_column(String(20))
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    parent: Mapped["WineCategory | None"] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[list["WineCategory"]] = relationship(
        back_populates="parent", order_by="WineCategory.position"
    )


class Wine(TimestampMixin, Base):
    """A wine of the shop's catalogue (session 9): the same cellar for every notebook, like the
    spices. It is filled and kept up to date by `scripts.sync_vinoseleccion`, which reads each
    page of the shop; nobody creates, edits or deletes wines from the app. Each notebook marks
    favourites and recommends wines for its recipes (`favorites`, `recipe_wines`)."""

    __tablename__ = "wines"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop: Mapped[str] = mapped_column(
        String(30), default=SHOP_VINOSELECCION, nullable=False, index=True
    )
    # The wine's page in the shop: its identity (the sync finds the wine by it)
    source_url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    winery: Mapped[str | None] = mapped_column(String(200))
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("wine_categories.id", ondelete="SET NULL")
    )
    # Facets
    sweetness: Mapped[str | None] = mapped_column(String(20))  # dry, off_dry, semi_sweet, sweet...
    body: Mapped[str | None] = mapped_column(String(10))  # light, medium, full
    ageing: Mapped[str | None] = mapped_column(String(20))  # young, oak, crianza, reserva...
    country: Mapped[str | None] = mapped_column(String(60))
    appellation: Mapped[str | None] = mapped_column(String(100))  # D.O. Ribera del Duero...
    grapes: Mapped[str | None] = mapped_column(String(200))
    vintage: Mapped[int | None] = mapped_column(Integer)
    price_range: Mapped[str | None] = mapped_column(String(4))  # €, €€, €€€, €€€€
    tasting_notes: Mapped[str | None] = mapped_column(Text)
    pairing_notes: Mapped[str | None] = mapped_column(Text)
    # The shop's name as people know it and its price the last time the page was read
    source_name: Mapped[str | None] = mapped_column(String(100))
    source_price: Mapped[float | None] = mapped_column(Numeric(8, 2))
    image_url: Mapped[str | None] = mapped_column(String(1000))
    # False when the shop no longer sells it (gone from its product list, or sold out)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    category: Mapped[WineCategory | None] = relationship()


class RecipeWine(Base):
    """Wine recommended for a recipe, with the reason."""

    __tablename__ = "recipe_wines"
    __table_args__ = (UniqueConstraint("recipe_id", "wine_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wine_id: Mapped[int] = mapped_column(
        ForeignKey("wines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(String(10), default="manual", nullable=False)  # imported
    added_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    wine: Mapped[Wine] = relationship()
    recipe: Mapped["Recipe"] = relationship()
    added_by: Mapped[User | None] = relationship()


class PairingRule(Base):
    """Recipe category → wine category, with the reason, for automatic suggestions."""

    __tablename__ = "pairing_rules"
    __table_args__ = (UniqueConstraint("recipe_category_id", "wine_category_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wine_category_id: Mapped[int] = mapped_column(
        ForeignKey("wine_categories.id", ondelete="CASCADE"), nullable=False
    )
    reason_es: Mapped[str] = mapped_column(String(200), nullable=False)
    reason_en: Mapped[str] = mapped_column(String(200), nullable=False)
    reason_fr: Mapped[str | None] = mapped_column(String(200))
    reason_nl: Mapped[str | None] = mapped_column(String(200))
    reason_de: Mapped[str | None] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    wine_category: Mapped[WineCategory] = relationship()
