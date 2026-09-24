"""Reading a wine from a shop page (schema.org Product) and from a bare page."""

from app.services.wine_importer import read_wine

SHOP = """<html><head><title>Viña Tondonia Reserva 2012 - Delatierra</title>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product",
"name":"Viña Tondonia Reserva 2012","brand":{"@type":"Brand","name":"López de Heredia"},
"image":"https://x.test/tondonia.jpg",
"description":"Tinto reserva de D.O.Ca. Rioja con tempranillo, garnacha, graciano y mazuelo. Seco.",
"offers":{"@type":"Offer","price":"38.90","priceCurrency":"EUR"}}</script></head>
<body><h1>Viña Tondonia Reserva 2012</h1></body></html>"""

FINO = """<html><head><title>Fino Solera Fina La Inglesa</title>
<script type="application/ld+json">{"@type":"Product","name":"Fino Solera Fina La Inglesa",
"brand":"Bodegas Pérez Barquero",
"description":"Fino de Montilla-Moriles, palomino... uva pedro ximénez, seco y punzante.",
"offers":{"@type":"Offer","price":"9,50"}}</script></head><body></body></html>"""

BARE = """<html><head><title>Albariño Pazo Señorans 2023 | Tienda</title>
<meta property="og:description" content="Blanco de Rías Baixas, 100% albariño. Fresco y aromático.">
<meta property="og:image" content="https://x.test/pazo.jpg"></head><body><p>hola</p></body></html>"""


def test_reads_a_product_page():
    w = read_wine(SHOP, "https://www.delatierra.com/x.html")
    assert w.name == "Viña Tondonia Reserva 2012" and w.winery == "López de Heredia"
    assert w.category_slug == "tinto-cuerpo-crianza" and w.ageing == "reserva"
    assert w.vintage == 2012 and w.price_range == "€€€" and w.source_price == 38.9
    assert w.source_name == "Delatierra"
    assert w.appellation.startswith("D.O.Ca. Rioja") and w.country == "España"
    assert w.grapes == "tempranillo, garnacha, graciano, mazuelo"
    assert w.sweetness == "dry" and w.image_url == "https://x.test/tondonia.jpg"
    assert w.warnings == []


def test_medium_dry_is_off_dry_not_dry():
    name = "Barbeito 5 years rainwater reserva medium dry"
    page = SHOP.replace("Viña Tondonia Reserva 2012", name)
    w = read_wine(page.replace(" Seco.", ""), "https://www.delatierra.com/x.html")
    assert w.sweetness == "off_dry" and w.ageing == "reserva"
    sweet = read_wine(page.replace("medium dry", "medium sweet"), "https://x.test/y.html")
    assert sweet.sweetness == "semi_sweet"


def test_reads_a_fino_and_a_page_without_product_data():
    fino = read_wine(FINO, "https://shop.test/fino")
    assert fino.category_slug == "fino-manzanilla" and fino.price_range == "€"
    assert fino.appellation == "Montilla-Moriles" and "pedro ximénez" in fino.grapes

    bare = read_wine(BARE, "https://shop.test/pazo")
    assert "no_product_data" in bare.warnings and "no_winery" in bare.warnings
    assert bare.name == "Albariño Pazo Señorans 2023" and bare.vintage == 2023
    assert bare.category_slug == "blanco-aromatico" and bare.appellation == "Rías Baixas"
    assert bare.image_url == "https://x.test/pazo.jpg"


# The shape of a real shop page (session 8): the shop as "brand", the name as "description",
# and the facts as label + value pairs inside the purchase form.
SHEET = """<html><head><title>Zarate 2024</title>
<meta property="og:site_name" content="Delatierra">
<script type="application/ld+json">{"@context":"https://schema.org/","@type":"Product",
"name":"Zarate 2024","description":"Zarate 2024","brand":{"@type":"Thing","name":"Delatierra"},
"image":"https://x.test/zarate.jpg",
"offers":{"@type":"Offer","priceCurrency":"EUR","price":"15.13"}}</script></head>
<body><form><div class="product-description"><p>Zarate 2024</p></div>
<span class="product-3words"><span>Profundo, afilado, tentador</span></span>
<div class="product-description-nofilter"><p>Eulogio Pomares es uno de los personajes más
importantes del vino gallego. Un albariño de viñas viejas del Val do Salnés, tenso y salino,
con tres meses sobre lías que le dan volumen sin quitarle frescura.</p></div>
<div class="product-profile-features"><div class="row">
<div class="profile-item"><h4>Bodega</h4><a href="/x">Bodegas Zarate</a></div>
<div class="profile-item"><h4>Origen</h4><a href="/y">D.O. Rias Baixas</a>
<span class="product-country">España</span></div>
<div class="profile-item"><h4>Tipo de vino</h4><a href="/z">Blanco</a></div>
<div class="profile-item"><h4>Crianza</h4><span>3 meses sobre lías</span></div>
<div class="profile-item"><h4>Grado alcohólico</h4><span>12,5º</span></div>
</div></div></form></body></html>"""


def test_reads_the_data_sheet_of_a_shop_page():
    w = read_wine(SHEET, "https://www.delatierra.com/todos-los-vinos/13588-zarate-2024.html")
    assert w.name == "Zarate 2024" and w.winery == "Bodegas Zarate"
    assert w.appellation == "D.O. Rias Baixas" and w.country == "España"
    assert w.source_name == "Delatierra" and w.source_price == 15.13 and w.price_range == "€€"
    assert w.tasting_notes.startswith("Eulogio Pomares") and "albariño" in w.tasting_notes
    assert w.category_slug == "blanco-aromatico" and w.grapes == "albariño"
    assert w.vintage == 2024 and w.warnings == []
