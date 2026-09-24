"""Reading Vinoselección's pages (session 9), with small pages built like the shop's."""

from app.services import vinoseleccion

# The menu repeats the sheet's labels as filters: they must not be taken for the wine's
MENU = """<nav><ul><li>Tipo de vino</li><li>Tinto</li><li>País</li><li>Francia</li>
<li>Variedad de uva</li><li>Mencía</li></ul></nav>"""


def page(name, price, sheet, *, stock='"is_in_stock":"Yes"', extra=""):
    return f"""<html><head><title>{name}</title>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Product",
"name":"{name}","description":"","image":"https://x.test/{price}.jpg",
"offers":{{"@type":"Offer","price":{price},"priceCurrency":"EUR",
"availability":"https://schema.org/InStock"}}}}</script>
<script>window.dataLayer=[{{"event":"view_item","ecommerce":{{"items":[{{"item_name":"{name}",
{stock}}}]}}}}];</script></head><body>{MENU}
<h1>{name}</h1><div class="price">{price} €</div><button>Añadir al carrito</button>
<p>{name} es un vino muy rico.</p>{sheet}{extra}
<h2>Compra con total confianza</h2><p>Más de 180.000 clientes</p></body></html>"""


VICALANDA = page(
    "La Vicalanda Reserva 2021",
    23,
    """<h3>Características de consumo</h3><div>Maridaje</div><div><p>La <b>Vicalanda</b>
Reserva es el acompañante ideal para el cordero asado.</p></div><div>Temperatura servicio</div>
<div>16 – 18ºC</div><h3>Características generales</h3><div>Tipo de vino</div>
<div>Tinto Reserva</div><div>Región</div><div>D.O.Ca. Rioja</div><div>Variedad de uva</div>
<div>100%</div><div>Tempranillo</div><div>Permanencia en barrica</div><div>14 meses</div>
<div>Capacidad (cl)</div><div>75</div><h3>Notas de cata</h3><p>Granate intenso.</p>
<p>Frutos negros y violetas.</p><h3>La bodega</h3><div>Bodega</div>
<div>Bodegas Bilbaínas</div><div>Enólogo</div><div>Diego Pinilla</div>""",
)
CAVA = page(
    "Cava Gran Bach Brut",
    7.95,
    """<h3>Características generales</h3><div>Tipo de vino</div><div>Espumoso Blanco</div>
<div>Región</div><div>D.O. Cava</div><div>Variedad de uva</div><div>Macabeo</div>
<div>, 0%</div><div>Xarel·lo</div><div>, 0%</div><div>Parellada</div>""",
)
OLD = page(
    "Marqués de Cáceres Rosado 2013",
    4.5,
    """<h3>Características generales</h3><div>Tipo de vino</div><div>Rosado</div>""",
    stock="",
)


def test_reads_the_sheet_after_the_cart_button_not_the_menu():
    sheet = vinoseleccion.read_sheet(VICALANDA)
    assert sheet["type"] == "Tinto Reserva" and sheet["appellation"] == "D.O.Ca. Rioja"
    assert sheet["grapes"] == "tempranillo" and sheet["winery"] == "Bodegas Bilbaínas"
    assert sheet["pairing"] == "La Vicalanda Reserva es el acompañante ideal para el cordero asado."
    assert sheet["description"] == "Granate intenso. Frutos negros y violetas."
    assert "country" not in sheet  # "Francia" was a menu filter


def test_reads_a_wine_for_sale():
    wine = vinoseleccion.read(VICALANDA, "https://www.vinoseleccion.com/la-vicalanda-reserva-2021")
    assert wine.name == "La Vicalanda Reserva 2021" and wine.in_stock is True
    assert wine.category_slug == "tinto-cuerpo-crianza" and wine.ageing == "reserva"
    assert wine.source_price == 23 and wine.source_name == "Vinoselección"
    assert wine.country == "España" and wine.vintage == 2021 and wine.grapes == "tempranillo"
    assert wine.pairing_notes.startswith("La Vicalanda Reserva es el acompañante")
    assert wine.tasting_notes == "Granate intenso. Frutos negros y violetas."


def test_a_cava_is_a_cava_and_grapes_lose_their_percentages():
    wine = vinoseleccion.read(CAVA, "https://www.vinoseleccion.com/gran-bach-brut-cava")
    assert wine.category_slug == "cava" and wine.sweetness == "brut"
    assert wine.grapes == "macabeo, xarel·lo, parellada"


def test_an_old_page_is_not_on_sale_even_if_the_offer_says_in_stock():
    wine = vinoseleccion.read(OLD, "https://www.vinoseleccion.com/marques-de-caceres-rosado-2013")
    assert wine.in_stock is False and wine.category_slug == "rosado-fruta"
    sold_out = page("X", 9, "", stock='"is_in_stock":"No"')
    assert vinoseleccion.in_stock(sold_out) is False
