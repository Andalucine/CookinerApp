"""Fill someone's notebook with fifty everyday recipes, importing each one from its page on
directoalpaladar.com with the app's own importer (session 9), to try the notebook and the
weekly menu with something real.

Run from `backend/` (in Docker, with `docker compose exec api` in front):

    python -m scripts.import_demo_recipes beatriz@correo.es

The list is in `scripts/catalog_data/demo_recipes.py`: each recipe gets the category, the
moment (course tag) and the seasons written there, and keeps the link to the page and the
site's name. Recipes already in the notebook (same page) are skipped, so it can be run again.
The notebook needs a plan that imports (`scripts.set_plan`). Development only; it needs the
network to reach the site, and takes a couple of minutes (one page at a time)."""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Category, Recipe, Season, Tag, User
from app.services import import_job, importer
from app.services import recipe as recipe_service
from scripts.catalog_data.demo_recipes import DEMO_RECIPES, SITE


class UnknownUser(Exception):
    pass


def _id(db: Session, model, column, value: str) -> int:
    found = db.scalar(select(model.id).where(column == value))
    if found is None:
        raise LookupError(f"{model.__name__} {value!r} is not in the catalogue")
    return found


def import_all(
    db: Session, email: str, recipes=DEMO_RECIPES, echo=print
) -> tuple[list[str], list[str]]:
    """Import the recipes missing from the person's notebook; return (titles, failed urls)."""
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        raise UnknownUser
    notebook = user.notebook
    import_job.require_import(notebook)
    existing = set(db.scalars(select(Recipe.source_url).where(Recipe.notebook_id == notebook.id)))
    added: list[str] = []
    failed: list[str] = []
    for path, category_slug, course, seasons in recipes:
        url = SITE + path
        if url in existing:
            continue
        try:
            job, _warnings, draft = import_job.start(db, user, notebook, url)
        except (importer.InvalidUrl, importer.FetchFailed, importer.NoRecipeFound) as exc:
            failed.append(url)
            echo(f"  ✗ {type(exc).__name__}: {url}")
            continue
        draft.category_ids = [_id(db, Category, Category.slug, category_slug)]
        draft.tag_ids = (
            [db.scalar(select(Tag.id).where(Tag.kind == "course", Tag.code == course))]
            if course
            else []
        )
        draft.season_ids = [_id(db, Season, Season.code, code) for code in seasons]
        recipe = import_job.save(db, user, job, notebook, draft)
        added.append(recipe.title)
        echo(f"  ✓ {recipe.title} ({category_slug})")
    return added, failed


def main(args: list[str], db: Session | None = None) -> int:
    if len(args) != 1:
        print(__doc__)
        return 1
    session = db or SessionLocal()
    try:
        added, failed = import_all(session, args[0])
    except UnknownUser:
        print(f"✗ No hay ninguna cuenta con el correo {args[0]}")
        return 1
    except import_job.ImportNotInPlan:
        print("✗ El plan del cuaderno no importa de webs. Cambia el plan con scripts.set_plan")
        return 1
    except recipe_service.RecipeLimitReached:
        print("✗ El cuaderno ha llegado al máximo de recetas de su plan")
        return 1
    finally:
        if db is None:
            session.close()
    print(f"Recetas añadidas: {len(added)} · no se pudieron leer: {len(failed)}")
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
