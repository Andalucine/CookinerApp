"""Spice zone output models: families, cards, equivalence rules, substitutions and blends."""

from pydantic import BaseModel, ConfigDict


class SpiceFamilyOut(BaseModel):
    code: str
    name_es: str
    name_en: str
    count: int


class SpiceSummary(BaseModel):
    """One line of the spice list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    name_en: str | None = None
    aliases: str | None = None
    family: str | None = None
    has_substitutions: bool = False
    is_blend: bool = False


class EquivalenceRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    situation_es: str
    situation_en: str
    equivalence_es: str
    equivalence_en: str
    note_es: str | None = None
    note_en: str | None = None


class SubstitutionOut(BaseModel):
    substitute_es: str
    substitute_en: str
    substitute_id: int | None = None  # set when the substitute is a single catalogue ingredient
    ratio: str | None = None
    note_es: str | None = None
    note_en: str | None = None
    in_my_pantry: bool | None = None  # only when asked with login (recipe spices)


class BlendItemOut(BaseModel):
    ingredient_id: int
    name: str
    name_en: str | None = None
    parts: str
    is_optional: bool


class BlendOut(BaseModel):
    id: int
    ingredient_id: int
    name: str
    name_en: str | None = None
    quick_substitute_es: str | None = None
    quick_substitute_en: str | None = None
    note_es: str | None = None
    note_en: str | None = None
    items: list[BlendItemOut]


class BlendRef(BaseModel):
    """A blend this spice is part of."""

    ingredient_id: int
    name: str
    name_en: str | None = None


class SpiceCard(SpiceSummary):
    """The full card: what to use instead, how to make it at home, where it appears."""

    substitutions: list[SubstitutionOut]
    blend: BlendOut | None = None
    used_in_blends: list[BlendRef] = []


class RecipeSpiceOut(BaseModel):
    """An ingredient of a recipe that has a card in the spice zone."""

    ingredient_id: int
    name: str
    in_my_pantry: bool
    substitutions: list[SubstitutionOut]
    is_blend: bool
