"""Wine type tree (two levels) and automatic pairing rules (approved in session 4)."""

# (slug, name_es, name_en, serving_temp, [(slug, name_es, name_en, examples_es)])
WINE_TREE = [
    (
        "tintos",
        "Tintos",
        "Red wines",
        "14–18 °C",
        [
            ("tinto-joven", "Tinto joven", "Young red", None),
            ("tinto-ligero", "Tinto ligero y afrutado", "Light, fruity red", None),
            ("tinto-medio", "Tinto de cuerpo medio", "Medium-bodied red", None),
            ("tinto-cuerpo-crianza", "Tinto con cuerpo y crianza", "Full-bodied, aged red", None),
        ],
    ),
    (
        "blancos",
        "Blancos",
        "White wines",
        "8–12 °C",
        [
            ("blanco-joven", "Blanco joven y fresco", "Young, crisp white", None),
            (
                "blanco-aromatico",
                "Blanco aromático",
                "Aromatic white",
                "albariño, verdejo, moscatel seco, gewürztraminer",
            ),
            ("blanco-crianza", "Blanco con crianza o fermentado en barrica", "Oaked white", None),
            ("blanco-naranja", "Blanco de maceración / naranja", "Orange wine", None),
        ],
    ),
    (
        "rosados",
        "Rosados",
        "Rosé wines",
        "10–12 °C",
        [
            ("rosado-palido", "Rosado pálido y seco", "Pale, dry rosé", None),
            (
                "rosado-fruta",
                "Rosado de color y fruta",
                "Fruity rosé",
                "claretes, rosados de Navarra",
            ),
        ],
    ),
    (
        "espumosos",
        "Espumosos",
        "Sparkling wines",
        "6–8 °C",
        [
            ("cava", "Cava", "Cava", None),
            ("champan", "Champán", "Champagne", None),
            (
                "prosecco",
                "Prosecco y otros espumosos italianos",
                "Prosecco & Italian sparkling",
                None,
            ),
            (
                "otros-espumosos",
                "Otros espumosos",
                "Other sparkling",
                "crémant, sekt, espumosos ingleses",
            ),
            (
                "aguja",
                "Vinos de aguja y frizzantes",
                "Semi-sparkling",
                "txakoli, vinho verde, lambrusco",
            ),
        ],
    ),
    (
        "generosos",
        "Generosos y fortificados",
        "Fortified wines",
        "6–14 °C",
        [
            (
                "fino-manzanilla",
                "Fino y manzanilla",
                "Fino & manzanilla",
                "Jerez, Sanlúcar, Montilla-Moriles",
            ),
            ("amontillado", "Amontillado", "Amontillado", None),
            ("oloroso", "Oloroso", "Oloroso", None),
            ("palo-cortado", "Palo cortado", "Palo cortado", None),
            ("cream-medium", "Cream y medium", "Cream & medium sherry", None),
            ("oporto", "Oporto", "Port", None),
            ("madeira-marsala", "Madeira y Marsala", "Madeira & Marsala", None),
            ("vermut", "Vermut y aperitivos", "Vermouth & aperitifs", None),
        ],
    ),
    (
        "dulces",
        "Dulces y de postre",
        "Sweet & dessert wines",
        "8–10 °C",
        [
            ("pedro-ximenez", "Pedro Ximénez", "Pedro Ximénez", None),
            ("moscatel", "Moscatel", "Moscatel", "Málaga, Chipiona, Valencia"),
            ("malaga", "Vinos de Málaga", "Málaga wines", None),
            (
                "mistelas",
                "Mistelas y vinos de licor",
                "Mistelles & liqueur wines",
                "Condado de Huelva, Tarragona",
            ),
            (
                "vendimia-tardia",
                "Vinos de vendimia tardía y botritizados",
                "Late-harvest & botrytised",
                "Sauternes, Tokaji",
            ),
            ("vino-hielo", "Vinos de hielo", "Ice wines", None),
        ],
    ),
    (
        "otros",
        "Otros",
        "Other",
        None,
        [
            ("sin-alcohol", "Vinos sin alcohol o desalcoholizados", "Alcohol-free wines", None),
            ("sidra", "Sidra y perada", "Cider & perry", None),
            ("sake", "Sake y vinos de arroz", "Sake & rice wines", None),
            ("vinos-frutas", "Vinos de frutas", "Fruit wines", None),
        ],
    ),
]

# Facet values: defined once in app.models.wine (SWEETNESS, BODY, AGEING, PRICE_RANGES).

# (recipe category slug, [wine category slugs], reason_es, reason_en)
# Recipe category slugs are level-2 categories (or level-3 where the table is that specific).
PAIRING_RULES = [
    (
        "aperitivos-tapas",
        ["fino-manzanilla", "cava", "blanco-joven"],
        "Vinos secos y frescos que limpian el paladar entre bocados",
        "Dry, crisp wines that clean the palate between bites",
    ),
    (
        "ensaladas",
        ["blanco-joven", "rosado-palido", "fino-manzanilla"],
        "Acidez y frescura para acompañar el aliño",
        "Acidity and freshness to match the dressing",
    ),
    (
        "sopas-frias",
        ["blanco-joven", "rosado-palido", "fino-manzanilla"],
        "Vinos fríos y ligeros para platos fríos",
        "Cold, light wines for cold dishes",
    ),
    (
        "pescado-blanco",
        ["blanco-aromatico", "fino-manzanilla", "cava"],
        "Blancos aromáticos y finos realzan el pescado sin taparlo",
        "Aromatic whites and fino lift the fish without covering it",
    ),
    (
        "mariscos",
        ["blanco-aromatico", "fino-manzanilla", "cava"],
        "Albariño, verdejo o manzanilla: salinidad con salinidad",
        "Albariño, verdejo or manzanilla: salt with salt",
    ),
    (
        "pescado-azul",
        ["blanco-crianza", "rosado-fruta", "tinto-ligero"],
        "El pescado graso admite más cuerpo e incluso un tinto ligero",
        "Oily fish takes more body and even a light red",
    ),
    (
        "pescado-plancha-parrilla",
        ["blanco-crianza", "rosado-fruta", "tinto-ligero"],
        "El tostado de la parrilla pide un vino con algo de crianza",
        "The char of the grill calls for a wine with some oak",
    ),
    (
        "arroces-cereales",
        ["blanco-crianza", "rosado-fruta", "tinto-joven"],
        "Arroces y fideuá: vinos de cuerpo medio; los de marisco, blanco aromático",
        "Rice and fideuá: medium-bodied wines; seafood ones, aromatic white",
    ),
    (
        "fideua-fideos",
        ["blanco-aromatico", "rosado-fruta", "tinto-joven"],
        "La fideuá de marisco va con blanco aromático; la de carne, con tinto joven",
        "Seafood fideuá goes with aromatic white; meat fideuá with young red",
    ),
    (
        "pasta-salsa",
        ["tinto-ligero", "rosado-fruta"],
        "La acidez del tomate pide un tinto ligero y afrutado",
        "The acidity of tomato calls for a light, fruity red",
    ),
    (
        "pollo-aves",
        ["blanco-crianza", "tinto-medio"],
        "Aves: blanco con barrica o tinto de cuerpo medio",
        "Poultry: oaked white or medium-bodied red",
    ),
    (
        "cerdo",
        ["tinto-medio", "tinto-cuerpo-crianza"],
        "Cerdo e ibéricos: tinto crianza o reserva",
        "Pork and ibérico: crianza or reserva red",
    ),
    (
        "cordero-cabrito",
        ["tinto-cuerpo-crianza", "tinto-medio"],
        "El cordero pide tinto con cuerpo",
        "Lamb calls for a full-bodied red",
    ),
    (
        "guisos-carne",
        ["tinto-medio", "tinto-cuerpo-crianza"],
        "Guisos de carne: tinto crianza o reserva",
        "Meat stews: crianza or reserva red",
    ),
    (
        "caza",
        ["tinto-cuerpo-crianza", "oloroso", "amontillado"],
        "Caza: tinto potente o un generoso seco con crianza oxidativa",
        "Game: a powerful red or a dry, oxidatively aged sherry",
    ),
    (
        "casqueria",
        ["tinto-cuerpo-crianza", "oloroso", "amontillado"],
        "Casquería: tinto con cuerpo, oloroso o amontillado",
        "Offal: full-bodied red, oloroso or amontillado",
    ),
    (
        "legumbres",
        ["tinto-joven", "tinto-medio", "oloroso", "amontillado"],
        "Cocidos y potajes: tinto joven o crianza; también oloroso o amontillado",
        "Cocidos and potajes: young or crianza red; also oloroso or amontillado",
    ),
    (
        "guisos-mundo",
        ["blanco-aromatico", "cava", "rosado-fruta"],
        "Cocina picante o asiática: blanco aromático semiseco, riesling, cava o rosado",
        "Spicy or Asian food: off-dry aromatic white, riesling, cava or rosé",
    ),
    (
        "fideos-asiaticos",
        ["blanco-aromatico", "cava", "rosado-fruta"],
        "Picante y aromático: blanco semiseco, cava o rosado",
        "Spicy and aromatic: off-dry white, cava or rosé",
    ),
    (
        "tartas-bizcochos",
        ["moscatel", "cava", "malaga"],
        "Tartas y bizcochos: moscatel, cava semiseco o vinos de Málaga",
        "Cakes: moscatel, off-dry cava or Málaga wines",
    ),
    (
        "tartas-chocolate-brownies",
        ["pedro-ximenez", "oporto", "oloroso"],
        "Chocolate: Pedro Ximénez, oporto u oloroso dulce",
        "Chocolate: Pedro Ximénez, port or sweet oloroso",
    ),
    (
        "chocolate-bombones",
        ["pedro-ximenez", "oporto", "oloroso"],
        "Chocolate: Pedro Ximénez, oporto u oloroso dulce",
        "Chocolate: Pedro Ximénez, port or sweet oloroso",
    ),
    (
        "postres-frutas",
        ["moscatel", "vendimia-tardia", "cava"],
        "Postres de frutas: moscatel, vendimia tardía o cava dulce",
        "Fruit desserts: moscatel, late harvest or sweet cava",
    ),
    (
        "helados-sorbetes",
        ["moscatel", "vendimia-tardia", "cava"],
        "Helados: moscatel, vendimia tardía o cava dulce",
        "Ice creams: moscatel, late harvest or sweet cava",
    ),
    (
        "dulces-tradicionales",
        ["pedro-ximenez", "moscatel", "cream-medium"],
        "Turrón, polvorones y dulces de almendra: Pedro Ximénez, moscatel o cream",
        "Nougat, polvorones and almond sweets: Pedro Ximénez, moscatel or cream sherry",
    ),
]
