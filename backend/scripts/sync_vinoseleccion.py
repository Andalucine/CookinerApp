"""Fill and update the app's cellar with the wines of Vinoselección (session 9: CookinerApp acts
as its sales agent, so the cellar is the shop's catalogue, the same for every notebook).

Run from `backend/` (in Docker, with `docker compose exec api` in front):

    python -m scripts.sync_vinoseleccion                # everything (about 20-30 minutes)
    python -m scripts.sync_vinoseleccion --limit 10 --dry-run   # try 10 pages, save nothing
    python -m scripts.sync_vinoseleccion --url https://www.vinoseleccion.com/la-vicalanda-reserva-2021

What it does, step by step:
1. Reads the shop's product list (its sitemap, which its robots.txt offers to robots).
2. Leaves out what is not a single wine by its address: Enolobox boxes, the quarterly and
   monthly selections, collections, lots and gift cards.
3. Opens each page calmly (one every 1.5 seconds, so the shop is not overloaded) and reads it
   with the app's wine reader plus what is particular to this shop (`app.services.vinoseleccion`:
   its data sheet and whether it is on sale): name, winery, type, D.O., grapes, vintage, price,
   stock, photo, tasting notes and pairing.
4. Saves the wines that can be bought: new ones are added and the ones already there are
   updated (price, stock, notes). Pages without a price, not on sale (sold out, or old pages
   the shop keeps: most of its product list) or whose type cannot be told are not saved; the
   summary lists the ones without a type so they can be checked.
5. After a full run, the wines of the cellar that the shop no longer sells are marked as sold
   out (not deleted: a recipe may recommend them).

It needs the network to reach the shop, so it runs on the Mac, not in the tests.
"""

import argparse
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Wine
from app.models.wine import SHOP_VINOSELECCION
from app.services import importer, vinoseleccion, wine_importer
from app.services import wine as wine_service

SHOP_HOST = "https://www.vinoseleccion.com"
SITEMAP = f"{SHOP_HOST}/media/sitemap/com/sitemap.xml"
DELAY_SECONDS = 1.5

# Addresses that are not a single wine (subscription boxes, selections, collections...)
_NOT_A_WINE_URL = re.compile(
    r"enolobox|seleccion-(?:trimestral|mensual|privada|especial)|coleccion|colecciones"
    r"|lote-|-lote\b|pack-|-pack\b|estuche|tarjeta|regalo|suscripcion|club-|/catalog/"
    r"|-(?:ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)20\d\d$",
    re.I,
)
# Names that are not a single wine, whatever the address says
_NOT_A_WINE_NAME = re.compile(
    r"\b(?:colecci[oó]n|selecci[oó]n (?:trimestral|mensual|privada)|lote|estuche|pack"
    r"|enolobox|tarjeta regalo|caja de|suscripci[oó]n)\b",
    re.I,
)

Fetch = Callable[[str], tuple[str, str]]


@dataclass
class Report:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    not_wine: list[str] = field(default_factory=list)  # by address or name
    no_price: list[str] = field(default_factory=list)
    sold_out: list[str] = field(default_factory=list)
    no_type: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)  # the page could not be opened
    gone: list[str] = field(default_factory=list)  # in the cellar, no longer for sale


def _locations(xml: str) -> list[str]:
    return [loc.strip() for loc in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml)]


def product_urls(fetch: Fetch | None = None) -> list[str]:
    """Every product address of the shop, from its sitemap (an index of sitemaps: only the
    product ones are read). Repeated addresses once, in order."""
    fetch = fetch or wine_importer.fetch_html
    _, index = fetch(SITEMAP)
    children = _locations(index)
    if "<sitemapindex" in index:
        urls: list[str] = []
        for child in children:
            if "product" in child:
                _, xml = fetch(child)
                urls += _locations(xml)
    else:
        urls = children
    return list(dict.fromkeys(u for u in urls if u.startswith(SHOP_HOST)))


def is_candidate(url: str) -> bool:
    return not _NOT_A_WINE_URL.search(url)


def read_one(db: Session, url: str, fetch: Fetch, report: Report, *, save: bool, echo=print):
    """Read one page and save it when it is a wine for sale. Returns the saved wine or None."""
    try:
        final_url, html = fetch(url)
    except (importer.InvalidUrl, importer.FetchFailed):
        report.failed.append(url)
        echo(f"  ✗ no se pudo abrir {url}")
        return None
    preview = vinoseleccion.read(html, final_url)
    name = preview.name or url
    if not preview.name or _NOT_A_WINE_NAME.search(preview.name):
        report.not_wine.append(url)
        echo(f"  · no es un vino suelto: {name}")
        return None
    if preview.source_price is None:
        report.no_price.append(url)
        echo(f"  · sin precio: {name}")
        return None
    if preview.in_stock is False:
        report.sold_out.append(url)
        echo(f"  · no está a la venta: {name}")
        return None
    if not preview.category_slug:
        report.no_type.append(url)
        echo(f"  ? sin tipo (revisar): {name}  {url}")
        return None
    data = wine_service.from_preview(db, preview, url)
    line = (
        f"{data.name} · {preview.category_slug} · {data.source_price:.2f} €"
        f"{' · ' + data.appellation if data.appellation else ''}"
        f"{' · ' + data.grapes if data.grapes else ''}"
    )
    if not save:
        report.added.append(data.name)
        echo(f"  ✓ (prueba) {line}")
        return None
    wine, created = wine_service.upsert(db, data, SHOP_VINOSELECCION)
    (report.added if created else report.updated).append(data.name)
    echo(f"  {'+' if created else '↻'} {line}")
    return wine


def sync(
    db: Session,
    urls: list[str] | None = None,
    *,
    fetch: Fetch | None = None,
    sleep: Callable[[float], None] = time.sleep,
    delay: float = DELAY_SECONDS,
    limit: int | None = None,
    dry_run: bool = False,
    echo=print,
) -> Report:
    fetch = fetch or wine_importer.fetch_html
    report = Report()
    full_run = urls is None and limit is None and not dry_run
    if urls is None:
        urls = product_urls(fetch)
        echo(f"Fichas en el mapa de la tienda: {len(urls)}")
    candidates = [u for u in urls if is_candidate(u)]
    report.not_wine += [u for u in urls if not is_candidate(u)]
    if limit is not None:
        candidates = candidates[:limit]
    echo(f"Fichas que se van a leer: {len(candidates)}")
    for position, url in enumerate(candidates, start=1):
        if position > 1:
            sleep(delay)
        read_one(db, url, fetch, report, save=not dry_run, echo=echo)
        if not dry_run and position % 25 == 0:
            db.commit()  # progress is kept if the run is stopped halfway
            echo(f"— {position} de {len(candidates)}")
    if full_run:
        # Gone: no longer in the shop's list, or read now as sold out / not a wine for sale.
        # A page that failed to open keeps its wine as it was (it may be a network hiccup).
        not_for_sale = set(report.sold_out) | set(report.no_price) | set(report.no_type)
        for_sale = set(candidates) - not_for_sale - set(report.not_wine)
        for wine in db.scalars(
            select(Wine).where(Wine.shop == SHOP_VINOSELECCION, Wine.in_stock.is_(True))
        ):
            if wine.source_url not in for_sale:
                wine.in_stock = False
                report.gone.append(wine.name)
    if not dry_run:
        db.commit()
    return report


def _summary(report: Report, echo=print) -> None:
    echo("")
    echo(f"✓ Vinos nuevos: {len(report.added)}")
    echo(f"↻ Vinos actualizados: {len(report.updated)}")
    if report.gone:
        echo(f"⚠ Ya no se venden (marcados como agotados): {len(report.gone)}")
    echo(
        f"· No están a la venta (agotados o fichas antiguas; no se guardan): {len(report.sold_out)}"
    )
    echo(f"· Sin precio (no se guardan): {len(report.no_price)}")
    echo(f"· No son un vino suelto (cajas, selecciones, colecciones): {len(report.not_wine)}")
    if report.no_type:
        echo(f"? Sin tipo, para revisar ({len(report.no_type)}):")
        for url in report.no_type:
            echo(f"    {url}")
    if report.failed:
        echo(f"✗ No se pudieron abrir ({len(report.failed)}): se reintentan en la próxima vez")


def main(args: list[str], db: Session | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.sync_vinoseleccion")
    parser.add_argument("--limit", type=int, help="leer solo las N primeras fichas")
    parser.add_argument("--dry-run", action="store_true", help="leer sin guardar nada")
    parser.add_argument("--url", action="append", help="leer solo esta ficha (se puede repetir)")
    parser.add_argument("--delay", type=float, default=DELAY_SECONDS, help="segundos entre fichas")
    options = parser.parse_args(args)
    session = db or SessionLocal()
    try:
        report = sync(
            session,
            urls=options.url,
            limit=options.limit,
            dry_run=options.dry_run,
            delay=options.delay,
        )
    except (importer.InvalidUrl, importer.FetchFailed):
        print("✗ No se ha podido leer el mapa de productos de Vinoselección. ¿Hay conexión?")
        return 1
    finally:
        if db is None:
            session.close()
    _summary(report)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
