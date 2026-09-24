"""Wine type tree (two levels) and automatic pairing rules (approved in session 4)."""

# (slug, name_es, name_en, serving_temp, [(slug, name_es, name_en, examples_es)])
WINE_TREE = [
    (
        "tintos",
        "Tintos",
        "Red wines",
        "14–18 °C",
        [
            (
                "tinto-joven",
                "Tinto joven",
                "Young red",
                "Rioja joven, Valdepeñas, Beaujolais, mencía joven",
            ),
            (
                "tinto-ligero",
                "Tinto ligero y afrutado",
                "Light, fruity red",
                "Pinot noir, garnacha de Gredos, Bierzo (mencía), Bardolino",
            ),
            (
                "tinto-medio",
                "Tinto de cuerpo medio",
                "Medium-bodied red",
                "Rioja crianza, Chianti, Côtes du Rhône, bobal (Utiel-Requena)",
            ),
            (
                "tinto-cuerpo-crianza",
                "Tinto con cuerpo y crianza",
                "Full-bodied, aged red",
                "Ribera del Duero reserva, Priorat, Toro, Barolo, cabernet sauvignon",
            ),
        ],
    ),
    (
        "blancos",
        "Blancos",
        "White wines",
        "8–12 °C",
        [
            (
                "blanco-joven",
                "Blanco joven y fresco",
                "Young, crisp white",
                "Vinho verde, pinot grigio, Muscadet, airén joven, chardonnay sin madera",
            ),
            (
                "blanco-aromatico",
                "Blanco aromático",
                "Aromatic white",
                "Albariño (Rías Baixas), verdejo (Rueda), godello, riesling, gewürztraminer",
            ),
            (
                "blanco-crianza",
                "Blanco con crianza o fermentado en barrica",
                "Oaked white",
                "Rioja blanco con crianza, chardonnay con barrica, Borgoña blanco (Meursault)",
            ),
            (
                "blanco-naranja",
                "Blanco de maceración / naranja",
                "Orange wine",
                "Blancos de maceración del Penedès, Georgia (qvevri), Friuli-Collio",
            ),
        ],
    ),
    (
        "rosados",
        "Rosados",
        "Rosé wines",
        "10–12 °C",
        [
            (
                "rosado-palido",
                "Rosado pálido y seco",
                "Pale, dry rosé",
                "Provenza, rosados pálidos de Navarra y Rioja, «piel de cebolla»",
            ),
            (
                "rosado-fruta",
                "Rosado de color y fruta",
                "Fruity rosé",
                "Claretes de Cigales, rosados de Navarra, Tavel, Rioja rosado clásico",
            ),
        ],
    ),
    (
        "espumosos",
        "Espumosos",
        "Sparkling wines",
        "6–8 °C",
        [
            ("cava", "Cava", "Cava", "D.O. Cava: Penedès, Requena, Extremadura, Rioja"),
            ("champan", "Champán", "Champagne", "Champagne (Reims, Épernay, Aÿ)"),
            (
                "prosecco",
                "Prosecco y otros espumosos italianos",
                "Prosecco & Italian sparkling",
                "Prosecco, Franciacorta, Trento, Asti spumante",
            ),
            (
                "otros-espumosos",
                "Otros espumosos",
                "Other sparkling",
                "Corpinnat, Clàssic Penedès, Crémant, Sekt, espumosos ingleses",
            ),
            (
                "aguja",
                "Vinos de aguja y frizzantes",
                "Semi-sparkling",
                "Txakoli, Vinho verde con aguja, Lambrusco, Moscato d'Asti",
            ),
        ],
    ),
    (
        "generosos",
        "Generosos secos (Jerez y Montilla)",
        "Dry fortified (sherry-style)",
        "7–14 °C",
        [
            (
                "fino-manzanilla",
                "Fino y manzanilla",
                "Fino & manzanilla",
                "Jerez (fino), Sanlúcar de Barrameda (manzanilla), Montilla-Moriles (fino)",
            ),
            ("amontillado", "Amontillado", "Amontillado", "Jerez, Montilla-Moriles"),
            ("oloroso", "Oloroso", "Oloroso", "Jerez, Montilla-Moriles"),
            ("palo-cortado", "Palo cortado", "Palo cortado", "Jerez"),
        ],
    ),
    (
        "licorosos",
        "Licorosos y fortificados",
        "Fortified & liqueur wines",
        "10–16 °C",
        [
            (
                "cream-medium",
                "Cream, medium y pale cream",
                "Cream, medium & pale cream",
                "Generosos de licor de Jerez (Bristol Cream, medium, pale cream)",
            ),
            ("oporto", "Oporto", "Port", "Oporto (ruby, tawny, LBV, vintage)"),
            (
                "madeira-marsala",
                "Madeira y Marsala",
                "Madeira & Marsala",
                "Madeira (sercial, verdelho, bual, malvasía), Marsala",
            ),
            (
                "mistelas",
                "Mistelas y vinos de licor",
                "Mistelles & liqueur wines",
                "Mistelas del Condado de Huelva y Tarragona, moscatel de licor de Alicante",
            ),
        ],
    ),
    (
        "dulces",
        "Dulces naturales y de postre",
        "Sweet & dessert wines",
        "8–14 °C",
        [
            (
                "pedro-ximenez",
                "Pedro Ximénez",
                "Pedro Ximénez",
                "Jerez, Montilla-Moriles (vino dulce natural)",
            ),
            (
                "moscatel",
                "Moscatel",
                "Moscatel",
                "Chipiona, Málaga, Jerez, Setúbal (dulces naturales)",
            ),
            (
                "malaga",
                "Vinos de Málaga",
                "Málaga wines",
                "Málaga dulce, Málaga trasañejo, Pajarete",
            ),
            (
                "rancios-fondillon",
                "Rancios y fondillón",
                "Rancio wines & fondillón",
                "Fondillón de Alicante, rancios del Empordà y del Priorat",
            ),
            (
                "vendimia-tardia",
                "Vinos de vendimia tardía y botritizados",
                "Late-harvest & botrytised",
                "Sauternes, Tokaji aszú, riesling Auslese y Beerenauslese",
            ),
            (
                "vino-hielo",
                "Vinos de hielo",
                "Ice wines",
                "Eiswein (Alemania, Austria), Icewine (Canadá)",
            ),
        ],
    ),
    (
        "otros",
        "Otros",
        "Other",
        None,
        [
            (
                "vermut",
                "Vermut y vinos aromatizados",
                "Vermouth & aromatised wines",
                "Vermut de Reus, de Jerez y de Turín; aperitivos aromatizados",
            ),
            (
                "sin-alcohol",
                "Vinos sin alcohol o desalcoholizados",
                "Alcohol-free wines",
                "Vinos 0,0 y desalcoholizados",
            ),
            (
                "sidra",
                "Sidra y perada",
                "Cider & perry",
                "Sidra natural asturiana, sidra vasca (sagardoa), perada",
            ),
            (
                "sake",
                "Sake y vinos de arroz",
                "Sake & rice wines",
                "Sake junmai y ginjo; vino de arroz chino (huangjiu)",
            ),
            (
                "vinos-frutas",
                "Vinos de frutas",
                "Fruit wines",
                "Vino de manzana, de cereza, de grosella",
            ),
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
