"""The shop's wines (session 9: Vinoselección), the wines recommended for a recipe and the
automatic pairing suggestion."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.catalog import Named


class WineIn(BaseModel):
    """A wine as read from its page in the shop, before the sync saves it."""

    name: str = Field(min_length=1, max_length=200)
    winery: str | None = Field(default=None, max_length=200)
    category_id: int | None = Field(default=None, description="Wine type (second level)")
    sweetness: str | None = Field(
        default=None,
        pattern="^(dry|off_dry|semi_sweet|sweet|brut_nature|extra_brut|brut|extra_dry|sec"
        "|demi_sec|doux)$",
    )
    body: str | None = Field(default=None, pattern="^(light|medium|full)$")
    ageing: str | None = Field(
        default=None, pattern="^(young|oak|crianza|reserva|gran_reserva|solera)$"
    )
    country: str | None = Field(default=None, max_length=60)
    appellation: str | None = Field(default=None, max_length=100, description="D.O. Rioja...")
    grapes: str | None = Field(default=None, max_length=200)
    vintage: int | None = Field(default=None, ge=1800, le=2100)
    price_range: str | None = Field(default=None, pattern="^(€|€€|€€€|€€€€)$")
    tasting_notes: str | None = None
    pairing_notes: str | None = None
    source_url: str | None = Field(default=None, max_length=1000)
    source_name: str | None = Field(default=None, max_length=100, description="The shop's name")
    source_price: float | None = Field(default=None, ge=0, description="Price in that shop, €")
    image_url: str | None = Field(default=None, max_length=1000)


class WineCategoryRef(Named):
    slug: str
    parent: Named | None = None  # the first-level type (Tintos, Blancos...)
    serving_temp: str | None = None


class WineSummary(BaseModel):
    """What a list returns: enough for the card."""

    id: int
    name: str
    winery: str | None = None
    category: WineCategoryRef | None = None
    appellation: str | None = None
    vintage: int | None = None
    price_range: str | None = None
    image_url: str | None = None
    source_name: str | None = None  # "Vinoselección"
    source_price: float | None = None  # euros, the last time the shop's page was read
    in_stock: bool = True
    # The page in the shop with the agent's code (settings.shop_link_params): "Comprar"
    shop_url: str
    is_favorite: bool = False


class WineOut(WineSummary):
    sweetness: str | None = None
    body: str | None = None
    ageing: str | None = None
    country: str | None = None
    grapes: str | None = None
    tasting_notes: str | None = None
    pairing_notes: str | None = None
    # What the pairing rules say this type of wine goes with (recipe categories), for the
    # card when the person has not written "con qué marida" (session 8)
    pairs_with_categories: list[Named] = []
    checked_at: datetime | None = None


class WineSearchResult(BaseModel):
    total: int
    items: list[WineSummary]


class RecipeWineIn(BaseModel):
    wine_id: int
    reason: str | None = Field(default=None, description="Why this wine goes with the recipe")


class RecipeWineOut(BaseModel):
    id: int
    wine: WineSummary
    reason: str | None = None
    origin: str  # manual | imported
    added_by: str | None = None


class PairingRuleOut(BaseModel):
    wine_category: WineCategoryRef
    reason_es: str
    reason_en: str
    reason_fr: str | None = None
    reason_nl: str | None = None
    reason_de: str | None = None


class PairingSuggestion(BaseModel):
    """Automatic suggestion from the pairing rules, when the recipe has no wines of its own."""

    based_on: Named  # recipe category whose rules were used (maybe the parent of the primary)
    wine_types: list[PairingRuleOut]
    # Wines of the shop of those types: the person's favourites first, then those in stock
    wines: list[WineSummary]


class RecipeWinesOut(BaseModel):
    recommended: list[RecipeWineOut]
    suggestion: PairingSuggestion | None = None


class WineRecipeOut(BaseModel):
    """A recipe this wine is recommended for (Ficha del vino → Marida con)."""

    link_id: int
    recipe_id: int
    title: str
    reason: str | None = None
    added_by: str | None = None


class WineCategoryCount(BaseModel):
    category_id: int
    count: int
