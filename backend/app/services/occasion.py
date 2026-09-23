"""Occasions (épocas): the preloaded ones plus each notebook's own."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Notebook, Occasion, User


class OccasionNotFound(Exception):
    pass


class OccasionExists(Exception):
    pass


class OccasionPreloaded(Exception):
    pass


def list_for(db: Session, notebook_id: int) -> list[Occasion]:
    """Preloaded first (in their order), then the notebook's own alphabetically."""
    rows = db.scalars(
        select(Occasion).where(
            or_(Occasion.notebook_id.is_(None), Occasion.notebook_id == notebook_id)
        )
    ).all()
    preloaded = sorted((o for o in rows if o.notebook_id is None), key=lambda o: o.id)
    own = sorted((o for o in rows if o.notebook_id is not None), key=lambda o: o.name_es.lower())
    return preloaded + own


def get(db: Session, occasion_id: int) -> Occasion:
    occasion = db.get(Occasion, occasion_id)
    if occasion is None:
        raise OccasionNotFound
    return occasion


def _clean(name: str) -> str:
    return " ".join(name.split())


def _check_unique(db: Session, notebook_id: int, name: str, exclude_id: int | None) -> None:
    """No two occasions with the same name (ignoring case) among the preloaded and the
    notebook's own, in Spanish or in English."""
    lowered = name.lower()
    q = select(Occasion.id).where(
        or_(Occasion.notebook_id.is_(None), Occasion.notebook_id == notebook_id),
        or_(func.lower(Occasion.name_es) == lowered, func.lower(Occasion.name_en) == lowered),
    )
    if exclude_id is not None:
        q = q.where(Occasion.id != exclude_id)
    if db.scalar(q) is not None:
        raise OccasionExists


def create(db: Session, user: User, notebook: Notebook, name: str) -> Occasion:
    name = _clean(name)
    _check_unique(db, notebook.id, name, None)
    occasion = Occasion(
        notebook_id=notebook.id, name_es=name, name_en=name, is_preloaded=False,
        created_by_id=user.id,
    )  # fmt: skip
    db.add(occasion)
    db.commit()
    return occasion


def rename(db: Session, occasion: Occasion, name: str) -> Occasion:
    if occasion.notebook_id is None:
        raise OccasionPreloaded
    name = _clean(name)
    _check_unique(db, occasion.notebook_id, name, occasion.id)
    occasion.name_es = occasion.name_en = name
    db.commit()
    return occasion


def delete(db: Session, occasion: Occasion) -> None:
    """Recipes keep existing; they just lose this occasion."""
    if occasion.notebook_id is None:
        raise OccasionPreloaded
    db.delete(occasion)
    db.commit()
