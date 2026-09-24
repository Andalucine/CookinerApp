"""Spices added by a notebook and the notebook's own substitute lists (session 8). The
catalogue (`ingredients.is_spice`, `spice_substitutions`) is never changed here."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models import Ingredient, Notebook, NotebookSpice, NotebookSubstitution, User
from app.schemas.spice import (
    NotebookSpiceIn,
    NotebookSpiceOut,
    SubstitutionIn,
    SubstitutionOut,
)
from app.services import permissions
from app.services.recipe import get_or_create_ingredient, normalise_name


class SpiceNotFound(Exception):
    pass


class SpiceExists(Exception):
    """The name is already a catalogue spice or a spice of the notebook."""


class SelfSubstitute(Exception):
    """An ingredient cannot be its own substitute."""


# --- Own spices --------------------------------------------------------------------------


def _query():
    return select(NotebookSpice).options(
        selectinload(NotebookSpice.ingredient), selectinload(NotebookSpice.created_by)
    )


def to_out(spice: NotebookSpice, notebook: Notebook) -> NotebookSpiceOut:
    return NotebookSpiceOut(
        id=spice.id,
        notebook_id=spice.notebook_id,
        ingredient_id=spice.ingredient_id,
        name=spice.ingredient.name,
        family=spice.family,
        aliases=spice.aliases,
        added_by=permissions.added_by(notebook, spice.created_by),
        created_by_id=spice.created_by_id,
    )


def list_for(db: Session, notebook_id: int) -> list[NotebookSpice]:
    rows = db.scalars(_query().where(NotebookSpice.notebook_id == notebook_id)).all()
    return sorted(rows, key=lambda s: s.ingredient.name)


def by_ingredient(db: Session, notebook_id: int) -> dict[int, NotebookSpice]:
    return {s.ingredient_id: s for s in list_for(db, notebook_id)}


def get(db: Session, spice_id: int) -> NotebookSpice:
    spice = db.scalar(_query().where(NotebookSpice.id == spice_id))
    if spice is None:
        raise SpiceNotFound
    return spice


def _clean_aliases(aliases: str | None) -> str | None:
    if not aliases:
        return None
    parts = [normalise_name(a) for a in aliases.split(",")]
    parts = [a for a in parts if a]
    return ", ".join(dict.fromkeys(parts)) or None


def _check_name(db: Session, notebook_id: int, ingredient: Ingredient, exclude_id: int | None):
    if ingredient.is_spice:
        raise SpiceExists  # already in the catalogue: nothing to add
    q = select(NotebookSpice.id).where(
        NotebookSpice.notebook_id == notebook_id, NotebookSpice.ingredient_id == ingredient.id
    )
    if exclude_id is not None:
        q = q.where(NotebookSpice.id != exclude_id)
    if db.scalar(q) is not None:
        raise SpiceExists


def create(db: Session, user: User, notebook: Notebook, body: NotebookSpiceIn) -> NotebookSpice:
    ingredient = get_or_create_ingredient(db, body.name)
    _check_name(db, notebook.id, ingredient, None)
    spice = NotebookSpice(
        notebook_id=notebook.id,
        ingredient_id=ingredient.id,
        family=body.family,
        aliases=_clean_aliases(body.aliases),
        created_by_id=user.id,
    )
    db.add(spice)
    db.commit()
    return get(db, spice.id)


def update(db: Session, spice: NotebookSpice, body: NotebookSpiceIn) -> NotebookSpice:
    ingredient = get_or_create_ingredient(db, body.name)
    if ingredient.id != spice.ingredient_id:
        _check_name(db, spice.notebook_id, ingredient, spice.id)
        spice.ingredient_id = ingredient.id
    spice.family = body.family
    spice.aliases = _clean_aliases(body.aliases)
    db.commit()
    return get(db, spice.id)


def delete_spice(db: Session, spice: NotebookSpice) -> None:
    """Its own substitute list goes with it; recipes that use it keep the ingredient."""
    db.execute(
        delete(NotebookSubstitution).where(
            NotebookSubstitution.notebook_id == spice.notebook_id,
            NotebookSubstitution.ingredient_id == spice.ingredient_id,
        )
    )
    db.delete(spice)
    db.commit()


# --- Own substitute lists ------------------------------------------------------------------


def substitutions_for(
    db: Session, notebook_id: int, ingredient_ids: list[int], pantry: set[int] | None = None
) -> dict[int, list[NotebookSubstitution]]:
    rows = db.scalars(
        select(NotebookSubstitution)
        .options(selectinload(NotebookSubstitution.created_by))
        .where(
            NotebookSubstitution.notebook_id == notebook_id,
            NotebookSubstitution.ingredient_id.in_(ingredient_ids),
        )
        .order_by(NotebookSubstitution.ingredient_id, NotebookSubstitution.position)
    )
    out: dict[int, list[NotebookSubstitution]] = {}
    for row in rows:
        out.setdefault(row.ingredient_id, []).append(row)
    return out


def substitution_out(row: NotebookSubstitution, pantry: set[int] | None) -> SubstitutionOut:
    return SubstitutionOut(
        substitute_es=row.substitute,
        substitute_en=row.substitute,
        substitute_id=row.substitute_id,
        ratio=row.ratio,
        note_es=row.note,
        note_en=row.note,
        in_my_pantry=(row.substitute_id in pantry)
        if pantry is not None and row.substitute_id
        else None,  # noqa: E501
    )


def ingredient_ids_with_own_substitutions(db: Session, notebook_id: int) -> set[int]:
    return set(
        db.scalars(
            select(NotebookSubstitution.ingredient_id)
            .where(NotebookSubstitution.notebook_id == notebook_id)
            .distinct()
        )
    )


def _link(db: Session, text: str) -> int | None:
    """The substitute as a catalogue ingredient when the text is just one name."""
    norm = normalise_name(text)
    if not norm or any(sep in norm for sep in ("+", ",", " o ", " y ", "/")):
        return None
    found = db.scalar(select(Ingredient).where(Ingredient.name == norm))
    return found.id if found else None


def set_substitutions(
    db: Session, user: User, notebook: Notebook, ingredient: Ingredient, items: list[SubstitutionIn]
) -> list[NotebookSubstitution]:
    """Replace the notebook's list for this ingredient. Everything is checked before the old
    list is removed, so a refused list leaves the previous one in place."""
    prepared = []
    for pos, item in enumerate(items):
        text = " ".join(item.substitute.split())
        link = _link(db, text)
        if link == ingredient.id or normalise_name(text) == ingredient.name:
            raise SelfSubstitute
        prepared.append(
            NotebookSubstitution(
                notebook_id=notebook.id,
                ingredient_id=ingredient.id,
                substitute=text,
                substitute_id=link,
                ratio=" ".join(item.ratio.split()) if item.ratio and item.ratio.strip() else None,
                note=" ".join(item.note.split()) if item.note and item.note.strip() else None,
                position=pos,
                created_by_id=user.id,
            )
        )
    db.execute(
        delete(NotebookSubstitution).where(
            NotebookSubstitution.notebook_id == notebook.id,
            NotebookSubstitution.ingredient_id == ingredient.id,
        )
    )
    db.add_all(prepared)
    db.commit()
    return substitutions_for(db, notebook.id, [ingredient.id]).get(ingredient.id, [])


def clear_substitutions(db: Session, notebook_id: int, ingredient_id: int) -> bool:
    """Back to the catalogue's list. Returns whether there was anything to remove."""
    result = db.execute(
        delete(NotebookSubstitution).where(
            NotebookSubstitution.notebook_id == notebook_id,
            NotebookSubstitution.ingredient_id == ingredient_id,
        )
    )
    db.commit()
    return bool(result.rowcount)
