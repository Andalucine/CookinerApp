"""Spice zone output models: families, cards, equivalence rules, substitutions and blends."""

from pydantic import BaseModel, ConfigDict, Field


class SpiceFamilyOut(BaseModel):
    code: str
    name_es: str
    name_en: str
    name_fr: str | None = None
    name_nl: str | None = None
    name_de: str | None = None
    count: int


class SpiceSummary(BaseModel):
    """One line of the spice list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    name_en: str | None = None
    name_fr: str | None = None
    name_nl: str | None = None
    name_de: str | None = None
    aliases: str | None = None
    family: str | None = None
    has_substitutions: bool = False
    is_blend: bool = False
    # Blends of the notebook (session 8): the notebook's row, and whether it is a version of a
    # catalogue blend (True) or a blend of its own (False)
    notebook_blend_id: int | None = None
    is_own_version: bool = False
    added_by: str | None = None
    # A spice added by the notebook (session 8)
    notebook_spice_id: int | None = None


class EquivalenceRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    situation_es: str
    situation_en: str
    situation_fr: str | None = None
    situation_nl: str | None = None
    situation_de: str | None = None
    equivalence_es: str
    equivalence_en: str
    equivalence_fr: str | None = None
    equivalence_nl: str | None = None
    equivalence_de: str | None = None
    note_es: str | None = None
    note_en: str | None = None
    note_fr: str | None = None
    note_nl: str | None = None
    note_de: str | None = None


class SubstitutionOut(BaseModel):
    substitute_es: str
    substitute_en: str
    substitute_fr: str | None = None
    substitute_nl: str | None = None
    substitute_de: str | None = None
    substitute_id: int | None = None  # set when the substitute is a single catalogue ingredient
    ratio: str | None = None
    note_es: str | None = None
    note_en: str | None = None
    note_fr: str | None = None
    note_nl: str | None = None
    note_de: str | None = None
    in_my_pantry: bool | None = None  # only when asked with login (recipe spices)


class BlendItemOut(BaseModel):
    ingredient_id: int
    name: str
    name_en: str | None = None
    name_fr: str | None = None
    name_nl: str | None = None
    name_de: str | None = None
    parts: str
    is_optional: bool


class BlendOut(BaseModel):
    id: int | None = None  # catalogue row (None for a notebook blend)
    notebook_blend_id: int | None = None  # notebook row (None for a catalogue blend)
    notebook_id: int | None = None
    added_by: str | None = None  # "(añadido por NOMBRE)" when it is not the notebook owner
    created_by_id: int | None = None
    ingredient_id: int
    name: str
    name_en: str | None = None
    name_fr: str | None = None
    name_nl: str | None = None
    name_de: str | None = None
    quick_substitute_es: str | None = None
    quick_substitute_en: str | None = None
    quick_substitute_fr: str | None = None
    quick_substitute_nl: str | None = None
    quick_substitute_de: str | None = None
    note_es: str | None = None
    note_en: str | None = None
    note_fr: str | None = None
    note_nl: str | None = None
    note_de: str | None = None
    items: list[BlendItemOut]


class BlendRef(BaseModel):
    """A blend this spice is part of."""

    ingredient_id: int
    name: str
    name_en: str | None = None
    name_fr: str | None = None
    name_nl: str | None = None
    name_de: str | None = None


class SpiceCard(SpiceSummary):
    """The full card: what to use instead, how to make it at home, where it appears.
    `blend` is the notebook's version when it has one, otherwise the catalogue's;
    `catalog_blend` carries the catalogue's when both exist ("volver a la del catálogo")."""

    substitutions: list[SubstitutionOut]
    has_own_substitutions: bool = False  # the notebook's list replaces the catalogue's
    substitutions_added_by: str | None = None
    # "Va bien con" (session 8): the notebook's text when it has one, else the catalogue's
    pairs_with: str | None = None
    has_own_pairs_with: bool = False
    pairs_with_added_by: str | None = None
    blend: BlendOut | None = None
    catalog_blend: BlendOut | None = None
    used_in_blends: list[BlendRef] = []


class SubstitutionIn(BaseModel):
    substitute: str = Field(min_length=1, max_length=150)
    ratio: str | None = Field(default=None, max_length=60)
    note: str | None = Field(default=None, max_length=200)


class SubstitutionsIn(BaseModel):
    """The notebook's whole list for one ingredient (replaces the previous one)."""

    items: list[SubstitutionIn] = Field(min_length=1, max_length=20)
    notebook_id: int | None = Field(default=None, description="Default: your own notebook")


class NotebookSpiceIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    family: str = Field(
        pattern="^(herbs|seeds|barks_roots_flowers|peppers_chillies|paprikas|blends|salts_seasonings)$"
    )  # noqa: E501
    aliases: str | None = Field(default=None, max_length=300)


class NotebookSpiceCreate(NotebookSpiceIn):
    notebook_id: int | None = Field(default=None, description="Default: your own notebook")


class NotebookSpiceOut(BaseModel):
    id: int
    notebook_id: int
    ingredient_id: int
    name: str
    family: str
    aliases: str | None = None
    added_by: str | None = None
    created_by_id: int | None = None


class BlendItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parts: str = Field(default="1", min_length=1, max_length=10)
    is_optional: bool = False


class BlendIn(BaseModel):
    """What the person writes: the name, a note and the ingredients with their parts."""

    name: str = Field(min_length=1, max_length=100)
    note: str | None = Field(default=None, max_length=200)
    items: list[BlendItemIn] = Field(min_length=1, max_length=40)


class BlendCreate(BlendIn):
    notebook_id: int | None = Field(default=None, description="Default: your own notebook")


class RecipeSpiceOut(BaseModel):
    """An ingredient of a recipe that has a card in the spice zone."""

    ingredient_id: int
    name: str
    in_my_pantry: bool
    substitutions: list[SubstitutionOut]
    is_blend: bool


class PairingIn(BaseModel):
    """The notebook's "va bien con" for an ingredient: a short list of foods, as text."""

    pairs_with: str = Field(min_length=1, max_length=300)
    notebook_id: int | None = Field(default=None, description="Default: your own notebook")
