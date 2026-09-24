"""Put the local database up to date with the models WITHOUT deleting data (session 8).

Run from `backend/` (in Docker, with `docker compose exec api` in front):

    python -m scripts.sync_dev_schema

It creates the tables that are missing and adds the columns that are missing in existing
tables. It never drops or changes anything. Development only, until the first deployment:
after that, every change is an Alembic migration (rule 8 of the organisation rules). The
initial migration must still be updated by hand, for fresh installations.
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateColumn

import app.models  # noqa: F401  (register every table)
from app.core.database import Base, engine

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("sync_dev_schema")


def sync(target: Engine) -> tuple[list[str], list[str]]:
    """Returns (tables created, columns added as 'table.column')."""
    inspector = inspect(target)
    existing = set(inspector.get_table_names())
    created = [t.name for t in Base.metadata.sorted_tables if t.name not in existing]
    Base.metadata.create_all(target)  # only the missing ones

    added: list[str] = []
    inspector = inspect(target)
    with target.begin() as connection:
        for table in Base.metadata.sorted_tables:
            if table.name in created:
                continue
            present = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in present:
                    continue
                definition = CreateColumn(column).compile(dialect=target.dialect)
                connection.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {definition}"))
                added.append(f"{table.name}.{column.name}")
    return created, added


def main() -> None:
    created, added = sync(engine)
    log.info("Tablas creadas: %s", ", ".join(created) or "ninguna")
    log.info("Columnas añadidas: %s", ", ".join(added) or "ninguna")
    log.info("Base de datos al día.")


if __name__ == "__main__":
    main()
