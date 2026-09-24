"""Fill someone's cellar with one example of each wine type, importing each one from its page
in the shop with the app's own importer (session 8).

Run from `backend/` (in Docker, with `docker compose exec api` in front):

    python -m scripts.import_demo_wines beatriz@correo.es

The list is in `scripts/catalog_data/demo_wines.py`. Each wine is read from its page (name,
winery, D.O., price, notes...), gets the type written in the list and keeps the link to the
page, the shop's name and its price. Wines already in the notebook (same page) are skipped, so
it can be run again. The notebook needs a plan with wines (`scripts.set_plan`). Development
only; it needs the network to reach the shop."""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import User, Wine
from app.services import importer, wine_importer
from app.services import wine as wine_service
from scripts.catalog_data.demo_wines import DEMO_WINES, SHOP


class UnknownUser(Exception):
    pass


def import_all(
    db: Session, email: str, wines: list[tuple[str, str]] = DEMO_WINES, echo=print
) -> tuple[list[str], list[str]]:
    """Import the wines missing from the person's notebook; return (added names, failed urls)."""
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        raise UnknownUser
    notebook = user.notebook
    wine_service.require_wines(notebook)
    existing = set(db.scalars(select(Wine.source_url).where(Wine.notebook_id == notebook.id)))
    added: list[str] = []
    failed: list[str] = []
    for path, slug in wines:
        url = SHOP + path
        if url in existing:
            continue
        try:
            final_url, html = wine_importer.fetch_html(url)
        except (importer.InvalidUrl, importer.FetchFailed):
            failed.append(url)
            echo(f"  ✗ no se pudo abrir {url}")
            continue
        preview = wine_importer.read_wine(html, final_url)
        preview.category_slug = slug  # the type is decided by hand in the list
        data = wine_service.from_preview(db, preview, url)
        if data.name == "?":
            failed.append(url)
            echo(f"  ✗ sin nombre en {url}")
            continue
        wine_service.create(db, user, notebook, data)
        added.append(data.name)
        echo(f"  ✓ {data.name} ({slug})")
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
    except wine_service.WinesNotInPlan:
        print("✗ El cuaderno es del plan gratuito: sin bodega. Cambia el plan con scripts.set_plan")
        return 1
    finally:
        if db is None:
            session.close()
    if added:
        print(f"✓ Vinos añadidos: {len(added)}")
    else:
        print("✓ Los vinos de ejemplo ya estaban en la bodega")
    if failed:
        print(f"⚠ Sin importar ({len(failed)}): revisa las direcciones en la lista")
    return 1 if failed and not added else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
