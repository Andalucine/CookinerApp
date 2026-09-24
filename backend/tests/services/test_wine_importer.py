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


def test_reads_a_fino_and_a_page_without_product_data():
    fino = read_wine(FINO, "https://shop.test/fino")
    assert fino.category_slug == "fino-manzanilla" and fino.price_range == "€"
    assert fino.appellation == "Montilla-Moriles" and "pedro ximénez" in fino.grapes

    bare = read_wine(BARE, "https://shop.test/pazo")
    assert "no_product_data" in bare.warnings and "no_winery" in bare.warnings
    assert bare.name == "Albariño Pazo Señorans 2023" and bare.vintage == 2023
    assert bare.category_slug == "blanco-aromatico" and bare.appellation == "Rías Baixas"
    assert bare.image_url == "https://x.test/pazo.jpg"
