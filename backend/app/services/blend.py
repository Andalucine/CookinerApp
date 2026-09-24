"""Blends of a notebook (session 8): new blends and the notebook's own versions of catalogue
blends. The catalogue (`SpiceBlend`) is never changed here."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Notebook, NotebookBlend, NotebookBlendItem, SpiceBlend, User
from app.schemas.catalog import texts
from app.schemas.spice import BlendIn, BlendItemOut, BlendOut
from app.services import permissions
from app.services.recipe import get_or_create_ingredient


class BlendNotFound(Exception):
    pass


class BlendExists(Exception):
    """The notebook already has a blend (or a version) with that name."""


class BlendSameIngredient(Exception):
    """An ingredient of the blend is the blend itself."""


def _query():
    return select(NotebookBlend).options(
        selectinload(NotebookBlend.ingredient),
        selectinload(NotebookBlend.created_by),
        selectinload(NotebookBlend.items).selectinload(NotebookBlendItem.ingredient),
    )


def catalog_ids(db: Session) -> set[int]:
    return set(db.scalars(select(SpiceBlend.ingredient_id)))


def to_out(blend: NotebookBlend, notebook: Notebook) -> BlendOut:
    return BlendOut(
        id=None,
        notebook_blend_id=blend.id,
        notebook_id=blend.notebook_id,
        added_by=permissions.added_by(notebook, blend.created_by),
        created_by_id=blend.created_by_id,
        ingredient_id=blend.ingredient_id,
        name=blend.ingredient.name,
        **texts(blend.ingredient, es=False),
        note_es=blend.note,
        note_en=blend.note,
        items=[
            BlendItemOut(
                ingredient_id=it.ingredient_id,
                name=it.ingredient.name,
                **texts(it.ingredient, es=False),
                parts=it.parts,
                is_optional=it.is_optional,
            )
            for it in blend.items
        ],
    )


def list_for(db: Session, notebook_id: int) -> list[NotebookBlend]:
    rows = db.scalars(_query().where(NotebookBlend.notebook_id == notebook_id)).all()
    return sorted(rows, key=lambda b: b.ingredient.name)


def by_ingredient(db: Session, notebook_id: int) -> dict[int, NotebookBlend]:
    return {b.ingredient_id: b for b in list_for(db, notebook_id)}


def get(db: Session, blend_id: int) -> NotebookBlend:
    blend = db.scalar(_query().where(NotebookBlend.id == blend_id))
    if blend is None:
        raise BlendNotFound
    return blend


def _fill(db: Session, blend: NotebookBlend, body: BlendIn) -> None:
    blend.note = " ".join(body.note.split()) if body.note and body.note.strip() else None
    # Delete the old lines first (and flush), so that an ingredient kept in the new list does
    # not clash with its old row in the unique constraint
    for old in list(blend.items):
        db.delete(old)
    blend.items.clear()
    db.flush()
    seen: set[int] = set()
    for pos, item in enumerate(body.items):
        ingredient = get_or_create_ingredient(db, item.name)
        if ingredient.id == blend.ingredient_id:
            raise BlendSameIngredient
        if ingredient.id in seen:  # the same ingredient twice: keep the first
            continue
        seen.add(ingredient.id)
        blend.items.append(
            NotebookBlendItem(
                ingredient_id=ingredient.id,
                parts=item.parts.strip() or "1",
                is_optional=item.is_optional,
                position=pos,
            )
        )


def create(db: Session, user: User, notebook: Notebook, body: BlendIn) -> NotebookBlend:
    ingredient = get_or_create_ingredient(db, body.name)
    exists = db.scalar(
        select(NotebookBlend.id).where(
            NotebookBlend.notebook_id == notebook.id, NotebookBlend.ingredient_id == ingredient.id
        )
    )
    if exists is not None:
        raise BlendExists
    blend = NotebookBlend(
        notebook_id=notebook.id, ingredient_id=ingredient.id, created_by_id=user.id
    )
    db.add(blend)
    db.flush()
    _fill(db, blend, body)
    db.commit()
    return get(db, blend.id)


def update(db: Session, blend: NotebookBlend, body: BlendIn) -> NotebookBlend:
    ingredient = get_or_create_ingredient(db, body.name)
    if ingredient.id != blend.ingredient_id:
        clash = db.scalar(
            select(NotebookBlend.id).where(
                NotebookBlend.notebook_id == blend.notebook_id,
                NotebookBlend.ingredient_id == ingredient.id,
            )
        )
        if clash is not None:
            raise BlendExists
        blend.ingredient_id = ingredient.id
    _fill(db, blend, body)
    db.commit()
    return get(db, blend.id)


def delete(db: Session, blend: NotebookBlend) -> None:
    """For a version of a catalogue blend this means going back to the catalogue's."""
    db.delete(blend)
    db.commit()
