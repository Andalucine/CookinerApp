"""Wines to try the cellar with (session 8): one example of as many types of the tree as the
shop delatierra.com offers, each imported from its own page with the app's importer, so the
notebook keeps the link, the shop and its price.

Each line: (page address, type slug to use). The slug is given by hand because it is the
person who decides the type when importing; the importer only proposes one. Types the shop
does not sell (blanco de maceración, prosecco, mistelas, rancios, vinos de hielo, sin
alcohol, sidra, sake, vinos de frutas) have no example here.
"""

SHOP = "https://www.delatierra.com/"

DEMO_WINES: list[tuple[str, str]] = [
    # Tintos
    ("todos-los-vinos/13579-cortijo-aguilares-joven-2024.html", "tinto-joven"),
    ("todos-los-vinos/13572-las-rocas-de-san-alejandro-garnacha-2022.html", "tinto-ligero"),
    ("todos-los-vinos/13550-solabal-crianza-2021.html", "tinto-medio"),
    ("todos-los-vinos/13585-vizcarra-15-meses-2022.html", "tinto-cuerpo-crianza"),
    # Blancos
    ("todos-los-vinos/12958-ulises-chardonnay-2023-8410492004424.html", "blanco-joven"),
    ("todos-los-vinos/13588-zarate-2024.html", "blanco-aromatico"),
    ("todos-los-vinos/13260-guitian-fermentado-bca-2022-0000000001212.html", "blanco-crianza"),
    # Rosados
    ("todos-los-vinos/13546-la-novia-ideal-2024.html", "rosado-palido"),
    ("todos-los-vinos/13594-dos-flamencos-2023.html", "rosado-fruta"),
    # Espumosos
    ("todos-los-vinos/13505-carles-andreu-brut-nature.html", "cava"),
    ("todos-los-vinos/12837-delamotte-brut-3418760000678.html", "champan"),
    ("todos-los-vinos/12968-colet-navazos-reserva-extra-brut-2015.html", "otros-espumosos"),
    ("todos-los-vinos/13109-ceretto-moscato-asti-2024.html", "aguja"),
    # Generosos secos
    ("bodega-juan-pinero/13074-manzanilla-pasada-maruja-8437013429238.html", "fino-manzanilla"),
    ("todos-los-vinos/13654-amontillado-la-inglesa.html", "amontillado"),
    ("todos-los-vinos/12994-oloroso-greatduke-juan-pinero-8437013429290.html", "oloroso"),
    ("todos-los-vinos/12854-palo-cortado-greatduke-juan-pinero-8437013429283.html", "palo-cortado"),
    # Licorosos y fortificados
    ("bodega-juan-pinero/13075-cream-juan-pinero-8437013429245.html", "cream-medium"),
    ("todos-los-vinos/13217-niepoort-tawny-5602840010000.html", "oporto"),
    (
        "todos-los-vinos/12906-barbeito-5-years-rainwater-reserva-medium-dry-5601519346419.html",
        "madeira-marsala",
    ),
    # Dulces naturales y de postre
    ("todos-los-vinos/13073-pedro-ximenez-juan-pinero-8437013429153.html", "pedro-ximenez"),
    ("todos-los-vinos/13163-mr-2023.html", "moscatel"),
    ("todos-los-vinos/13154-molino-real-2021.html", "malaga"),
    ("todos-los-vinos/13779-oremus-aszu-3-puttonyos-2018.html", "vendimia-tardia"),
    # Otros
    ("todos-los-vinos/13717-vermut-capcanes.html", "vermut"),
]
