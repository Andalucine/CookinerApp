"""Reading recipe pages (no network: the pages are written here)."""

import json

import pytest

from app.services import importer

RECIPE = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "WebSite", "name": "Cocina de Prueba"},
        {
            "@type": ["Recipe"],
            "name": "Lentejas de la casa",
            "description": "<p>Unas lentejas &amp; su chorizo.</p>",
            "author": {"@type": "Person", "name": "Marta Prueba"},
            "publisher": {"@type": "Organization", "name": "Cocina de Prueba"},
            "image": [{"@type": "ImageObject", "url": "https://ejemplo.test/lentejas.jpg"}],
            "prepTime": "PT15M",
            "cookTime": "PT1H",
            "recipeYield": ["4", "4 raciones"],
            "recipeIngredient": [
                "300 g de lentejas pardinas",
                "2 dientes de ajo picados",
                "1 cucharadita de pimentón dulce",
                "Sal",
            ],
            "recipeInstructions": [
                {
                    "@type": "HowToSection",
                    "name": "El sofrito",
                    "itemListElement": [{"@type": "HowToStep", "text": "Picar y sofreír el ajo."}],
                },
                {"@type": "HowToStep", "text": "Añadir las lentejas y cubrir de agua."},
            ],
            "video": {
                "@type": "VideoObject",
                "embedUrl": "https://www.youtube.com/embed/abcdefghijk",
            },
        },
    ],
}


def page(data=RECIPE, extra=""):
    return (
        "<html><head><title>Lentejas | Cocina de Prueba</title>"
        '<meta property="og:site_name" content="Cocina de Prueba">'
        '<meta property="og:image" content="https://ejemplo.test/og.jpg">'
        f'<script type="application/ld+json">{json.dumps(data)}</script>'
        f"</head><body>{extra}</body></html>"
    )


def test_reads_json_ld_recipe():
    p = importer.read_recipe(page(), "https://ejemplo.test/lentejas")
    assert p.complete and p.title == "Lentejas de la casa"
    assert p.description == "Unas lentejas & su chorizo."
    assert p.source_name == "Cocina de Prueba" and p.cook_name == "Marta Prueba"
    assert p.prep_time_minutes == 75 and p.servings == 4
    assert p.image_url == "https://ejemplo.test/lentejas.jpg"
    assert p.youtube_url == "https://www.youtube.com/watch?v=abcdefghijk"
    assert p.instructions == (
        "EL SOFRITO\n1. Picar y sofreír el ajo.\n2. Añadir las lentejas y cubrir de agua."
    )
    first = p.ingredients[0]
    assert (first.quantity, first.unit, first.name) == (300, "g", "lentejas pardinas")
    assert first.raw_text == "300 g de lentejas pardinas"
    assert p.ingredients[3].name == "Sal" and p.ingredients[3].quantity is None


def test_without_recipe_data_gives_title_and_photo():
    iframe = '<iframe src="https://www.youtube-nocookie.com/embed/zyxwvutsrqp"></iframe>'
    p = importer.read_recipe(page(data={"@type": "WebPage"}, extra=iframe), "https://x.test/a")
    assert not p.complete and p.title == "Lentejas"  # " | Cocina de Prueba" removed
    assert p.image_url == "https://ejemplo.test/og.jpg"
    assert p.youtube_url == "https://www.youtube.com/watch?v=zyxwvutsrqp"
    with pytest.raises(importer.NoRecipeFound):
        importer.read_recipe("<html><body>nada</body></html>", "https://x.test/b")


@pytest.mark.parametrize(
    ("line", "quantity", "unit", "name"),
    [
        ("1½ kg de patatas", 1.5, "kg", "patatas"),
        ("500 g. de bonito (sin piel)", 500, "g", "bonito"),
        ("1/2 cucharadita de comino molido", 0.5, "cucharadita", "comino molido"),
        ("3-4 tomates maduros, rallados", 3, None, "tomates maduros"),
        ("200ml de leche", 200, "ml", "leche"),
        ("½ cebolla", 0.5, None, "cebolla"),
        ("Un chorrito de aceite", None, None, "Un chorrito de aceite"),
        ("6count Huevos", 6, "unidad", "Huevos"),
        ("2 o 3 filetes de lomo de cerdo", 2, "filete", "lomo de cerdo"),
        ("1 o 2 pimientos verdes (ver nota)", 1, None, "pimientos verdes"),
    ],
)
def test_ingredient_lines(line, quantity, unit, name):
    parsed = importer.parse_ingredient(line)
    assert (parsed.quantity, parsed.unit, parsed.name) == (quantity, unit, name)


def test_durations():
    assert importer.iso_minutes("PT1H30M") == 90
    assert importer.iso_minutes("P0DT0H20M") == 20
    assert importer.iso_minutes("20 minutos") is None


@pytest.mark.parametrize(
    "url",
    ["file:///etc/passwd", "ftp://ejemplo.test/x", "http://localhost/x", "http://127.0.0.1:8000/",
     "http://10.0.0.5/receta", "http://[::1]/"],
)  # fmt: skip
def test_private_or_odd_addresses_are_refused(url):
    with pytest.raises(importer.InvalidUrl):
        importer.fetch_html(url)


BLOG = """<html><head><title>Bocadillo de prueba - Blog de Prueba</title>
<meta property="og:site_name" content="Blog de Prueba">
<meta property="og:image" content="https://ejemplo.test/bocadillo.jpg"></head><body>
<nav><ul><li>Inicio</li><li>Recetas</li></ul></nav>
<h1>Bocadillo de prueba</h1><p>Una introducción larga sobre el bocadillo que no es parte de la
receta y que ocupa bastante más de noventa caracteres para no parecer un título.</p>
<h2>COMO HACER BOCADILLO DE PRUEBA</h2>
<p><strong>INGREDIENTES para 2 bocadillos:</strong></p>
<ul><li>2 o 3 filetes de lomo</li><li>1 pan de bocadillo</li><li>aceite de oliva</li></ul>
<p>Para el aliño:</p><ul><li>sal fina</li></ul>
<p>Un comentario después de la lista que tampoco es un paso de la receta.</p>
<p>1.- Freír los filetes en el aceite.</p><p>2.- Abrir el pan y montar el bocadillo.</p>
<h3>Otras recetas</h3><p>3. Esto ya no es de la receta.</p>
<footer><p>1. Aviso legal</p></footer></body></html>"""


def test_blog_without_recipe_data_is_read_from_its_text():
    p = importer.read_recipe(BLOG, "https://blog.test/bocadillo")
    assert p.complete and p.from_text
    assert p.title == "Bocadillo de prueba" and p.source_name == "Blog de Prueba"
    assert p.servings == 2
    assert [i.name for i in p.ingredients] == ["lomo", "pan de bocadillo", "aceite de oliva",
                                               "sal fina"]  # fmt: skip
    assert (
        p.instructions
        == "1. Freír los filetes en el aceite.\n2. Abrir el pan y montar el bocadillo."
    )


def test_steps_under_a_preparation_heading():
    html = (
        "<h2>Ingredientes</h2><ul><li>2 huevos</li></ul>"
        "<h2>Preparación</h2><ol><li>Batir.</li><li>Cuajar.</li></ol><h2>Notas</h2><p>x</p>"
    )
    p = importer.read_recipe(f"<title>Tortilla</title>{html}", "https://blog.test/t")
    assert p.instructions == "1. Batir.\n2. Cuajar."


def test_publisher_given_as_a_domain_uses_the_site_name():
    data = {**RECIPE["@graph"][1], "publisher": {"@type": "Organization", "name": "ejemplo.test"}}
    p = importer.read_recipe(page(data=data), "https://ejemplo.test/x")
    assert p.source_name == "Cocina de Prueba"


def test_site_name_from_the_json_ld_when_everything_else_is_a_domain():
    data = {
        "@graph": [
            {"@type": "WebSite", "name": "Cocina de Prueba", "url": "https://ejemplo.test"},
            {**RECIPE["@graph"][1], "publisher": {"@type": "Organization", "name": "ejemplo.test"}},
        ]
    }
    html = f'<script type="application/ld+json">{json.dumps(data)}</script>'
    p = importer.read_recipe(html, "https://ejemplo.test/x")
    assert p.source_name == "Cocina de Prueba"
    only_domain = {**RECIPE["@graph"][1], "publisher": {"name": "ejemplo.test"}}
    html = f'<script type="application/ld+json">{json.dumps(only_domain)}</script>'
    assert importer.read_recipe(html, "https://ejemplo.test/x").source_name == "ejemplo.test"


@pytest.mark.parametrize(
    ("headline", "name"),
    [
        (
            "Cómo hacer nigiri (o nigirizushi): todo lo que necesitas saber para hacerlos en casa",
            "Nigiri",
        ),
        ("Receta de lentejas con chorizo", "Lentejas con chorizo"),
        ("Salmorejo cordobés, receta tradicional paso a paso", "Salmorejo cordobés"),
        ("Tarta de queso | La mejor del mundo", "Tarta de queso"),
        ("Marmitako", "Marmitako"),
        ("Cómo hacer", "Cómo hacer"),  # nothing sensible left: keep it
    ],
)
def test_the_title_is_the_name_of_the_dish(headline, name):
    assert importer.short_title(headline) == name


def test_site_name_written_in_lowercase_is_capitalised():
    assert importer.nice_site_name("directo al paladar") == "Directo al Paladar"
    assert importer.nice_site_name("Recetas de Rechupete") == "Recetas de Rechupete"
    assert importer.nice_site_name("javirecetas.com") == "javirecetas.com"
    assert importer.nice_site_name(None) is None
