"""Spice zone: families, list, general rules, blends and the card of each spice.

Global catalogue, read-only, no login required (like /catalog). The spices of a specific recipe,
checked against the user's pantry, are in /recipes/{id}/spices.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import DbSession, Lang
from app.i18n import t
from app.schemas.spice import BlendOut, EquivalenceRuleOut, SpiceCard, SpiceFamilyOut, SpiceSummary
from app.services import spice as spice_service

router = APIRouter(prefix="/spices", tags=["spices"])


@router.get("/families", response_model=list[SpiceFamilyOut])
def families(db: DbSession) -> list[SpiceFamilyOut]:
    """The seven families, in the order of the spice zone, with how many spices each has."""
    names = {
        f: (t(f"spice_family.{f}", "es"), t(f"spice_family.{f}", "en"))
        for f in spice_service.FAMILIES
    }
    return spice_service.families(db, names)


@router.get("", response_model=list[SpiceSummary])
def list_spices(
    db: DbSession,
    family: str | None = Query(default=None, description="Family code, e.g. 'herbs'"),
    q: str | None = Query(default=None, description="Search in Spanish/English names and aliases"),
) -> list[SpiceSummary]:
    return spice_service.list_spices(db, family, q)


@router.get("/rules", response_model=list[EquivalenceRuleOut])
def rules(db: DbSession) -> list[EquivalenceRuleOut]:
    """General equivalences shown at the top of the zone (fresh → dried, whole → ground...)."""
    return spice_service.rules(db)


@router.get("/blends", response_model=list[BlendOut])
def blends(db: DbSession) -> list[BlendOut]:
    """Every blend with its composition to make it at home."""
    return spice_service.blends(db)


@router.get("/{ingredient_id}", response_model=SpiceCard)
def spice_card(ingredient_id: int, db: DbSession, lang: Lang) -> SpiceCard:
    """The card: substitutions with ratio and note, composition if it is a blend, and the blends
    it is part of. Also works for fresh ingredients with substitutions (garlic, onion...)."""
    try:
        return spice_service.card(db, ingredient_id)
    except spice_service.SpiceNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("spice_not_found", lang)) from None
