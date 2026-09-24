"""Spice zone: families, list, general rules, blends and the card of each spice.

Global catalogue, read-only, no login required (like /catalog). With a token and (optionally)
`notebook_id`, the list and the card also carry the notebook's own blends and versions
(session 8; they are changed in /blends). The spices of a specific recipe, checked against the
user's pantry, are in /recipes/{id}/spices.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import DbSession, Lang, OptionalUser
from app.i18n import t
from app.models import Notebook
from app.schemas.spice import BlendOut, EquivalenceRuleOut, SpiceCard, SpiceFamilyOut, SpiceSummary
from app.services import permissions
from app.services import spice as spice_service

router = APIRouter(prefix="/spices", tags=["spices"])


def _notebook(db, user, lang, notebook_id: int | None) -> Notebook | None:
    """The notebook whose blends are added: none without a token."""
    if user is None:
        return None
    try:
        return permissions.resolve_notebook(db, user, notebook_id, edit=False)
    except (permissions.NotebookNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("notebook_not_found", lang)) from None


@router.get("/families", response_model=list[SpiceFamilyOut])
def families(
    db: DbSession,
    user: OptionalUser,
    lang: Lang,
    notebook_id: int | None = Query(default=None, description="Notebook whose spices to count"),
) -> list[SpiceFamilyOut]:
    """The seven families, in the order of the spice zone, with how many spices each has
    (the notebook's own included when there is a token)."""
    names = {
        f: (t(f"spice_family.{f}", "es"), t(f"spice_family.{f}", "en"))
        for f in spice_service.FAMILIES
    }
    return spice_service.families(db, names, _notebook(db, user, lang, notebook_id))


@router.get("", response_model=list[SpiceSummary])
def list_spices(
    db: DbSession,
    user: OptionalUser,
    lang: Lang,
    family: str | None = Query(default=None, description="Family code, e.g. 'herbs'"),
    q: str | None = Query(default=None, description="Search in Spanish/English names and aliases"),
    notebook_id: int | None = Query(default=None, description="Notebook whose blends to add"),
) -> list[SpiceSummary]:
    return spice_service.list_spices(db, family, q, _notebook(db, user, lang, notebook_id))


@router.get("/rules", response_model=list[EquivalenceRuleOut])
def rules(db: DbSession) -> list[EquivalenceRuleOut]:
    """General equivalences shown at the top of the zone (fresh → dried, whole → ground...)."""
    return spice_service.rules(db)


@router.get("/blends", response_model=list[BlendOut])
def blends(db: DbSession) -> list[BlendOut]:
    """Every blend with its composition to make it at home."""
    return spice_service.blends(db)


@router.get("/{ingredient_id}", response_model=SpiceCard)
def spice_card(
    ingredient_id: int,
    db: DbSession,
    user: OptionalUser,
    lang: Lang,
    notebook_id: int | None = Query(default=None, description="Notebook whose blends to add"),
) -> SpiceCard:
    """The card: substitutions with ratio and note, composition if it is a blend (the notebook's
    version first), and the blends it is part of. Also works for fresh ingredients with
    substitutions (garlic, onion...)."""
    try:
        return spice_service.card(db, ingredient_id, _notebook(db, user, lang, notebook_id))
    except spice_service.SpiceNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("spice_not_found", lang)) from None
