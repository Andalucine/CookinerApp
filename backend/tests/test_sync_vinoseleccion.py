"""The script that fills the cellar with Vinoselección's wines (session 9), with a fake shop."""

from sqlalchemy import select

from app.models import Wine
from app.services import importer
from scripts import sync_vinoseleccion as sync_script
from tests.services.test_vinoseleccion import CAVA, OLD, VICALANDA, page

HOST = sync_script.SHOP_HOST
INDEX = f"""<?xml version="1.0"?><sitemapindex>
<sitemap><loc>{HOST}/media/sitemap/com/sitemap_product_com.xml</loc></sitemap>
<sitemap><loc>{HOST}/media/sitemap/com/sitemap_category_com.xml</loc></sitemap>
</sitemapindex>"""
PRODUCTS = f"""<urlset>
<url><loc>{HOST}/la-vicalanda-reserva-2021</loc></url>
<url><loc>{HOST}/gran-bach-brut-cava</loc></url>
<url><loc>{HOST}/enolobox-enero-2021</loc></url>
<url><loc>{HOST}/argentina-abr2016</loc></url>
<url><loc>{HOST}/coleccion-tintos-clasicos-espanoles</loc></url>
<url><loc>{HOST}/marques-de-caceres-rosado-2013</loc></url>
<url><loc>{HOST}/aceite-de-oliva</loc></url>
<url><loc>{HOST}/roto</loc></url>
<url><loc>{HOST}/la-vicalanda-reserva-2021</loc></url>
</urlset>"""
OIL = page("Aceite de oliva virgen extra", 9, "")


def _quiet(db, fetch, **options):
    return sync_script.sync(db, fetch=fetch, sleep=lambda _: None, echo=lambda *_: None, **options)


def _shop(pages):
    def fetch(url):
        if url == sync_script.SITEMAP:
            return url, INDEX
        if url.endswith("sitemap_product_com.xml"):
            return url, PRODUCTS
        if url in pages:
            return url, pages[url]
        raise importer.FetchFailed

    return fetch


PAGES = {
    f"{HOST}/la-vicalanda-reserva-2021": VICALANDA,
    f"{HOST}/gran-bach-brut-cava": CAVA,
    f"{HOST}/marques-de-caceres-rosado-2013": OLD,
    f"{HOST}/aceite-de-oliva": OIL,
}
TONDONIA, BACH = "La Vicalanda Reserva 2021", "Cava Gran Bach Brut"


def test_product_list_comes_from_the_sitemap_once_each():
    urls = sync_script.product_urls(_shop(PAGES))
    assert len(urls) == 8 and urls[0].endswith("la-vicalanda-reserva-2021")
    assert not sync_script.is_candidate(f"{HOST}/enolobox-enero-2021")
    assert not sync_script.is_candidate(f"{HOST}/argentina-abr2016")
    assert sync_script.is_candidate(f"{HOST}/la-vicalanda-reserva-2021")


def test_sync_saves_only_wines_for_sale_and_updates_them(seeded):
    pauses = []
    report = sync_script.sync(seeded, fetch=_shop(PAGES), sleep=pauses.append, echo=lambda *_: None)
    wines = {w.name: w for w in seeded.scalars(select(Wine))}
    assert set(wines) == {TONDONIA, BACH}
    tondonia = wines[TONDONIA]
    assert tondonia.source_url == f"{HOST}/la-vicalanda-reserva-2021"
    assert tondonia.source_name == "Vinoselección" and float(tondonia.source_price) == 23
    assert tondonia.in_stock and tondonia.checked_at and tondonia.category_id
    assert tondonia.pairing_notes.startswith("La Vicalanda")  # the shop's own text
    assert wines[BACH].pairing_notes  # without it, the pairing rules of its type
    assert len(report.added) == 2 and report.updated == []
    assert len(report.not_wine) == 3 and len(report.sold_out) == 1
    assert report.no_type == [f"{HOST}/aceite-de-oliva"]
    assert report.failed == [f"{HOST}/roto"]
    assert pauses == [sync_script.DELAY_SECONDS] * 4  # one pause between pages

    # Next time: the price changed and the fino is no longer on sale
    pages = {**PAGES, f"{HOST}/la-vicalanda-reserva-2021": VICALANDA.replace("23,", "21,")}
    del pages[f"{HOST}/gran-bach-brut-cava"]
    report = sync_script.sync(
        seeded, fetch=_shop(pages), sleep=lambda _: None, echo=lambda *_: None
    )
    assert report.updated == [TONDONIA] and report.added == []
    seeded.expire_all()
    wines = {w.name: w for w in seeded.scalars(select(Wine))}
    assert float(wines[TONDONIA].source_price) == 21
    # The cava page failed to open this time: it is not marked as gone for a network error
    assert wines[BACH].in_stock


def test_a_wine_the_shop_stopped_selling_is_marked_not_deleted(seeded):
    _quiet(seeded, _shop(PAGES))
    pages = {**PAGES, f"{HOST}/gran-bach-brut-cava": CAVA.replace('"is_in_stock":"Yes"', "")}
    report = _quiet(seeded, _shop(pages))
    assert report.gone == [BACH]
    cava = seeded.scalar(select(Wine).where(Wine.name == BACH))
    assert cava is not None and cava.in_stock is False


def test_dry_run_and_limit_save_nothing_and_mark_nothing(seeded):
    report = sync_script.sync(
        seeded, fetch=_shop(PAGES), sleep=lambda _: None, echo=lambda *_: None,
        dry_run=True, limit=2,
    )  # fmt: skip
    assert len(report.added) == 2 and seeded.scalar(select(Wine)) is None


def test_main_with_one_address(seeded, monkeypatch, capsys):
    monkeypatch.setattr(sync_script.wine_importer, "fetch_html", _shop(PAGES))
    assert (
        sync_script.main(["--url", f"{HOST}/gran-bach-brut-cava", "--delay", "0"], db=seeded) == 0
    )
    assert "Vinos nuevos: 1" in capsys.readouterr().out
