"""Shorten the titles of the recipes imported from the web in someone's notebook (session 9):
the same rule the importer applies now ("Empedrado de garbanzos, una receta súper fresquita…"
→ "Empedrado de garbanzos"), for the recipes imported before the rule improved.

Run from `backend/` (in Docker, with `docker compose exec api` in front):

    python -m scripts.retitle_imported beatriz@correo.es

Only recipes with source "web" change, and only when the short title differs. Development
only."""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Recipe, User
from app.services.importer import short_title


class UnknownUser(Exception):
    pass


def retitle(db: Session, email: str, echo=print) -> list[tuple[str, str]]:
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        raise UnknownUser
    changed: list[tuple[str, str]] = []
    recipes = db.scalars(
        select(Recipe).where(Recipe.notebook_id == user.notebook.id, Recipe.source_type == "web")
    )
    for recipe in recipes:
        short = short_title(recipe.title)[:200]
        if short != recipe.title:
            changed.append((recipe.title, short))
            echo(f"  {recipe.title}\n    → {short}")
            recipe.title = short
    db.commit()
    return changed


def main(args: list[str], db: Session | None = None) -> int:
    if len(args) != 1:
        print(__doc__)
        return 1
    session = db or SessionLocal()
    try:
        changed = retitle(session, args[0])
    except UnknownUser:
        print(f"✗ No hay ninguna cuenta con el correo {args[0]}")
        return 1
    finally:
        if db is None:
            session.close()
    print(f"Títulos acortados: {len(changed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
