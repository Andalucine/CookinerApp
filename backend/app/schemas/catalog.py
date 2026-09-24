"""Read-only catalogue models: categories, tags, seasons, occasions, sections, ingredients,
wine types and wine facets."""

from pydantic import BaseModel, ConfigDict

LANGS = ("es", "en", "fr", "nl", "de")


def texts(row, *bases: str, es: bool = True) -> dict[str, str | None]:
    """The five languages of one or more catalogue texts of a row, to spread into an output
    model: texts(category) → {name_es, name_en, name_fr, name_nl, name_de} (session 9).
    Spanish and English always exist; the others are None when the row is not translated
    (a notebook's own occasion, for instance) and the app then shows the English one.
    `es=False` leaves out the Spanish one (ingredients keep it in `name`)."""
    bases = bases or ("name",)
    langs = LANGS if es else LANGS[1:]
    return {
        f"{base}_{lang}": getattr(row, f"{base}_{lang}", None) for base in bases for lang in langs
    }


def local_text(row, lang: str, base: str = "name") -> str | None:
    """One catalogue text in the request language, English when that language has no
    translation, Spanish as the last resort."""
    return (
        getattr(row, f"{base}_{lang}", None)
        or getattr(row, f"{base}_en", None)
        or getattr(row, f"{base}_es", None)
    )


class Named(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name_es: str
    name_en: str
    name_fr: str | None = None
    name_nl: str | None = None
    name_de: str | None = None


class SeasonOut(Named):
    code: str


class OccasionOut(Named):
    is_preloaded: bool


class ShoppingSectionOut(Named):
    code: str
    position: int


class TagOut(Named):
    kind: str
    code: str


class CategoryOut(Named):
    slug: str
    level: int
    examples_es: str | None = None
    children: list["CategoryOut"] = []


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    name_en: str | None = None
    name_fr: str | None = None
    name_nl: str | None = None
    name_de: str | None = None
    is_spice: bool
    shopping_section_id: int | None = None


class WineCategoryOut(Named):
    slug: str
    examples_es: str | None = None
    serving_temp: str | None = None
    children: list["WineCategoryOut"] = []


class FacetValue(BaseModel):
    code: str
    name_es: str
    name_en: str
    name_fr: str | None = None
    name_nl: str | None = None
    name_de: str | None = None


class WineFacetsOut(BaseModel):
    sweetness: list[FacetValue]
    body: list[FacetValue]
    ageing: list[FacetValue]
    price_ranges: list[str]
