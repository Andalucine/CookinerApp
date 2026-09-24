"""Session 9, run once: the cellar stops being each notebook's and becomes Vinoselección's.

Run from `backend/` (in Docker, with `docker compose exec api` in front), BEFORE
`scripts.sync_vinoseleccion`:

    python -m scripts.switch_to_vinoseleccion

Step by step:
1. Deletes every wine of every notebook, and with them their recommendations in recipes and
   the favourites that pointed to them (decision of Beatriz: only Vinoselección's wines).
2. Removes from the `wines` table the columns of a notebook's wine (notebook, who added it,
   who edited it).
3. Adds the new columns (shop, in stock, last read) with `sync_dev_schema`, and makes the
   wine's page in the shop its identity (one wine per address).

It can be run again: what is already done is skipped. Development only (PostgreSQL).
"""

import sys

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.core.database import engine as default_engine
from scripts.sync_dev_schema import sync as sync_schema

OLD_COLUMNS = ("notebook_id", "added_by_id", "updated_by_id")


def switch(target: Engine, echo=print) -> int:
    """Returns how many wines were deleted."""
    with target.begin() as c:
        deleted = c.execute(text("SELECT count(*) FROM wines")).scalar() or 0
        c.execute(text("DELETE FROM recipe_wines"))
        c.execute(text("DELETE FROM favorites WHERE wine_id IS NOT NULL"))
        c.execute(text("DELETE FROM wines"))
    echo(f"Vinos borrados: {deleted}")

    present = {col["name"] for col in inspect(target).get_columns("wines")}
    old = [name for name in OLD_COLUMNS if name in present]
    with target.begin() as c:
        for name in old:
            c.execute(text(f"ALTER TABLE wines DROP COLUMN {name}"))
    echo(f"Columnas quitadas: {', '.join(old) or 'ninguna'}")

    _, added = sync_schema(target)
    echo(f"Columnas añadidas: {', '.join(added) or 'ninguna'}")

    if target.dialect.name == "postgresql":
        with target.begin() as c:
            c.execute(text("ALTER TABLE wines ALTER COLUMN source_url SET NOT NULL"))
            c.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS uq_wines_source_url ON wines (source_url)")
            )
            c.execute(text("CREATE INDEX IF NOT EXISTS ix_wines_shop ON wines (shop)"))
    echo("La bodega está lista para Vinoselección: ahora, python -m scripts.sync_vinoseleccion")
    return deleted


def main(args: list[str], target: Engine | None = None) -> int:
    if args:
        print(__doc__)
        return 1
    switch(target or default_engine)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
