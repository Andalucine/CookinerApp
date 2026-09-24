"""Free notes of a notebook: menus, tricks, suppliers, ideas."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Note, User
from app.schemas.note import NoteIn

PREVIEW_CHARS = 140


class NoteNotFound(Exception):
    pass


def _query():
    return select(Note).options(
        selectinload(Note.notebook), selectinload(Note.author), selectinload(Note.updated_by)
    )


def get(db: Session, note_id: int) -> Note:
    note = db.scalar(_query().where(Note.id == note_id))
    if note is None:
        raise NoteNotFound
    return note


def list_notes(
    db: Session, notebook_id: int, text: str | None, kind: str | None = None
) -> list[Note]:
    q = _query().where(Note.notebook_id == notebook_id)
    if kind:
        q = q.where(Note.kind == kind)
    if text:
        term = f"%{text.strip()}%"
        q = q.where(or_(Note.title.ilike(term), Note.content.ilike(term)))
    return list(db.scalars(q.order_by(Note.updated_at.desc(), Note.id.desc())))


def create(db: Session, author: User, notebook_id: int, data: NoteIn) -> Note:
    note = Note(
        notebook_id=notebook_id,
        author_id=author.id,
        updated_by_id=author.id,
        title=data.title,
        content=data.content,
        kind=data.kind,
    )
    db.add(note)
    db.commit()
    return get(db, note.id)


def update(db: Session, note: Note, editor: User, data: NoteIn) -> Note:
    note.title, note.content, note.kind = data.title, data.content, data.kind
    note.updated_by_id = editor.id
    db.commit()
    return get(db, note.id)


def delete(db: Session, note: Note) -> None:
    db.delete(note)
    db.commit()


def preview(content: str | None) -> str | None:
    if not content:
        return None
    flat = " ".join(content.split())
    return flat if len(flat) <= PREVIEW_CHARS else flat[: PREVIEW_CHARS - 1].rstrip() + "…"
