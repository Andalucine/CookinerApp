"""Va bien con: the foods each catalogue spice is recommended with (session 8).

name → (Spanish, English). Short lists, in the order a cook would think of them.
"""

PAIRINGS = {
    # --- Hierbas aromáticas ---
    "perejil": (
        "pescado, marisco, patatas, huevos, salsa verde, ajo",
        "fish, seafood, potatoes, eggs, green sauce, garlic",
    ),
    "cilantro fresco": (
        "guacamole, ceviche, curry, sopas asiáticas, lima, pollo",
        "guacamole, ceviche, curry, Asian soups, lime, chicken",
    ),
    "albahaca": (
        "tomate, mozzarella, pasta, pesto, calabacín, fresas",
        "tomato, mozzarella, pasta, pesto, courgette, strawberries",
    ),
    "orégano": (
        "pizza, tomate, cordero, aceitunas, queso feta, adobos",
        "pizza, tomato, lamb, olives, feta, marinades",
    ),
    "tomillo": (
        "pollo asado, patatas, setas, guisos, conejo, miel",
        "roast chicken, potatoes, mushrooms, stews, rabbit, honey",
    ),
    "romero": (
        "cordero, patatas asadas, pan, cerdo, pollo, aceite",
        "lamb, roast potatoes, bread, pork, chicken, oil",
    ),
    "laurel": (
        "guisos, legumbres, caldos, escabeches, arroz, pescado en salsa",
        "stews, pulses, stocks, escabeche, rice, fish in sauce",
    ),
    "menta": (
        "cordero, guisantes, ensaladas, yogur, té, chocolate",
        "lamb, peas, salads, yoghurt, tea, chocolate",
    ),
    "eneldo": (
        "salmón, pepino, patatas, yogur, huevos, encurtidos",
        "salmon, cucumber, potatoes, yoghurt, eggs, pickles",
    ),
    "estragón": (
        "pollo, huevos, salsa bearnesa, pescado, mostaza, vinagre",
        "chicken, eggs, béarnaise, fish, mustard, vinegar",
    ),
    "cebollino": (
        "huevos, patatas, queso fresco, ensaladas, sopas frías, pescado",
        "eggs, potatoes, soft cheese, salads, cold soups, fish",
    ),
    "salvia": (
        "cerdo, mantequilla, calabaza, pasta rellena, hígado, alubias",
        "pork, butter, pumpkin, filled pasta, liver, beans",
    ),
    "mejorana": (
        "tomate, carnes picadas, setas, sopas, pollo, verduras asadas",
        "tomato, minced meat, mushrooms, soups, chicken, roast vegetables",
    ),
    "ajedrea": (
        "alubias, lentejas, cerdo, conejo, guisos, verduras",
        "beans, lentils, pork, rabbit, stews, vegetables",
    ),
    "perifollo": (
        "huevos, pescado blanco, ensaladas, cremas, pollo, zanahoria",
        "eggs, white fish, salads, cream soups, chicken, carrot",
    ),
    "hojas de hinojo": (
        "pescado, sardinas, cerdo, ensaladas, naranja, patatas",
        "fish, sardines, pork, salads, orange, potatoes",
    ),
    "hierba limón": (
        "curry tailandés, sopas, pollo, marisco, leche de coco, infusiones",
        "Thai curry, soups, chicken, seafood, coconut milk, teas",
    ),
    "hojas de lima kaffir": (
        "curry, sopa tom yum, pescado, arroz, leche de coco, pollo",
        "curry, tom yum soup, fish, rice, coconut milk, chicken",
    ),
    "hojas de curry": (
        "lentejas, arroz, pescado, patatas, coco, salteados indios",
        "lentils, rice, fish, potatoes, coconut, Indian stir-fries",
    ),
    "epazote": (
        "frijoles, quesadillas, sopas mexicanas, maíz, setas, marisco",
        "black beans, quesadillas, Mexican soups, corn, mushrooms, seafood",
    ),
    # --- Semillas ---
    "comino": (
        "garbanzos, cordero, chili, arroz, hummus, verduras asadas",
        "chickpeas, lamb, chili, rice, hummus, roast vegetables",
    ),
    "cilantro en grano": (
        "cerdo, encurtidos, pan, lentejas, curry, cítricos",
        "pork, pickles, bread, lentils, curry, citrus",
    ),
    "hinojo en grano": (
        "cerdo, salchichas, pescado, pan, tomate, col",
        "pork, sausages, fish, bread, tomato, cabbage",
    ),
    "anís": (
        "repostería, pan, higos, licores, pescado, guisos de cerdo",
        "pastries, bread, figs, liqueurs, fish, pork stews",
    ),
    "anís estrellado": (
        "cerdo estofado, pato, caldos asiáticos, pera, chocolate, arroz",
        "braised pork, duck, Asian broths, pear, chocolate, rice",
    ),
    "semillas de mostaza": (
        "encurtidos, curry, col, patatas, cerdo, aliños",
        "pickles, curry, cabbage, potatoes, pork, dressings",
    ),
    "sésamo": (
        "pollo, atún, ensaladas, pan, verduras salteadas, miel",
        "chicken, tuna, salads, bread, stir-fried vegetables, honey",
    ),
    "alcaravea": (
        "col, pan de centeno, cerdo, queso, patatas, remolacha",
        "cabbage, rye bread, pork, cheese, potatoes, beetroot",
    ),
    "nigella": (
        "pan naan, berenjena, lentejas, encurtidos, queso, calabaza",
        "naan bread, aubergine, lentils, pickles, cheese, pumpkin",
    ),
    "fenogreco": (
        "curry, lentejas, patatas, pan, encurtidos, pollo",
        "curry, lentils, potatoes, bread, pickles, chicken",
    ),
    "semillas de amapola": (
        "pan, bollería, ensaladas, pasta, limón, aliños",
        "bread, pastries, salads, pasta, lemon, dressings",
    ),
    "cardamomo": (
        "arroz, café, repostería, pollo, leche, naranja",
        "rice, coffee, pastries, chicken, milk, orange",
    ),
    "cardamomo negro": (
        "guisos de carne, arroz biryani, lentejas, caldos, cordero",
        "meat stews, biryani rice, lentils, broths, lamb",
    ),
    "semillas de apio": (
        "ensaladas, tomate, encurtidos, sopas, pollo, salsas",
        "salads, tomato, pickles, soups, chicken, sauces",
    ),
    "enebro": (
        "caza, cerdo, col, ginebra, patés, marinadas",
        "game, pork, cabbage, gin, pâtés, marinades",
    ),
    # --- Cortezas, raíces y flores ---
    "canela": (
        "arroz con leche, manzana, cordero, chocolate, café, calabaza",
        "rice pudding, apple, lamb, chocolate, coffee, pumpkin",
    ),
    "casia": (
        "cerdo estofado, pato, compotas, café, arroz, chocolate",
        "braised pork, duck, compotes, coffee, rice, chocolate",
    ),
    "jengibre molido": (
        "galletas, calabaza, curry, zanahoria, pollo, té",
        "biscuits, pumpkin, curry, carrot, chicken, tea",
    ),
    "cúrcuma": (
        "arroz, coliflor, lentejas, pollo, huevos, leche dorada",
        "rice, cauliflower, lentils, chicken, eggs, golden milk",
    ),
    "galanga": (
        "sopas tailandesas, curry, marisco, pollo, leche de coco",
        "Thai soups, curry, seafood, chicken, coconut milk",
    ),
    "regaliz": (
        "postres, helados, cerdo, pato, chocolate, infusiones",
        "desserts, ice cream, pork, duck, chocolate, teas",
    ),
    "azafrán": (
        "paella, arroz, marisco, pescado, sopas, leche y postres",
        "paella, rice, seafood, fish, soups, milk desserts",
    ),
    "clavo": (
        "jamón asado, compotas, arroz, cebolla, vino caliente, caza",
        "roast ham, compotes, rice, onion, mulled wine, game",
    ),
    "nuez moscada": (
        "bechamel, espinacas, patatas, puré, pasta rellena, huevos",
        "béchamel, spinach, potatoes, mash, filled pasta, eggs",
    ),
    "macis": (
        "bechamel, pescado, pollo, bollería, patés, sopas",
        "béchamel, fish, chicken, pastries, pâtés, soups",
    ),
    "vainilla": (
        "natillas, helados, bizcochos, fruta asada, chocolate, marisco",
        "custards, ice cream, sponges, roast fruit, chocolate, seafood",
    ),
    "lavanda": (
        "cordero, miel, bizcochos, helados, melocotón, limón",
        "lamb, honey, sponges, ice cream, peach, lemon",
    ),
    "agua de azahar": (
        "roscón, bollería, ensaladas de naranja, natillas, té",
        "roscón, pastries, orange salads, custards, tea",
    ),
    "agua de rosas": (
        "postres de leche, baklava, fresas, helados, pistacho",
        "milk desserts, baklava, strawberries, ice cream, pistachio",
    ),
    "zumaque": (
        "ensaladas, cebolla, pollo, pescado, hummus, kebab",
        "salads, onion, chicken, fish, hummus, kebab",
    ),
    # --- Pimientas y picantes ---
    "pimienta negra": (
        "carnes, pasta, huevos, quesos, fresas, casi todo lo salado",
        "meat, pasta, eggs, cheese, strawberries, almost anything savoury",
    ),
    "pimienta blanca": (
        "salsas claras, puré, pescado, sopas cremosas, pollo",
        "pale sauces, mash, fish, cream soups, chicken",
    ),
    "pimienta verde": (
        "solomillo, pato, salsas de nata, pescado, patés",
        "sirloin, duck, cream sauces, fish, pâtés",
    ),
    "pimienta rosa": (
        "salmón, ensaladas, queso fresco, fresas, pato, vinagretas",
        "salmon, salads, soft cheese, strawberries, duck, vinaigrettes",
    ),
    "pimienta de jamaica": (
        "adobos, guisos caribeños, encurtidos, repostería, jamón, calabaza",
        "marinades, Caribbean stews, pickles, baking, ham, pumpkin",
    ),
    "pimienta de sichuan": (
        "pollo kung pao, cerdo, berenjena, tofu, fideos, salteados",
        "kung pao chicken, pork, aubergine, tofu, noodles, stir-fries",
    ),
    "pimienta larga": (
        "guisos de carne, quesos, chocolate, fruta asada, caldos",
        "meat stews, cheese, chocolate, roast fruit, broths",
    ),
    "cayena": (
        "gambas al ajillo, salsas picantes, huevos, chocolate, legumbres",
        "garlic prawns, hot sauces, eggs, chocolate, pulses",
    ),
    "guindilla seca": (
        "gambas al ajillo, pasta, aceite de guindilla, bacalao, legumbres",
        "garlic prawns, pasta, chilli oil, cod, pulses",
    ),
    "copos de guindilla": (
        "pizza, pasta, verduras asadas, huevos, aceites",
        "pizza, pasta, roast vegetables, eggs, oils",
    ),
    "ñora": (
        "romesco, arroces, fideuá, guisos de pescado, salmorreta",
        "romesco, rice dishes, fideuá, fish stews, salmorreta",
    ),
    "pimiento choricero": (
        "bacalao a la vizcaína, guisos, patatas a la riojana, marmitako",
        "cod a la vizcaína, stews, Riojan potatoes, marmitako",
    ),
    "chile chipotle": (
        "carnes a la brasa, mayonesas, frijoles, salsas, pollo",
        "grilled meat, mayonnaise, beans, sauces, chicken",
    ),
    "chile ancho": (
        "mole, enchiladas, chili, guisos de cerdo, chocolate",
        "mole, enchiladas, chili, pork stews, chocolate",
    ),
    "chile de árbol": (
        "salsas mexicanas, aceites, cacahuetes, tacos, encurtidos",
        "Mexican salsas, oils, peanuts, tacos, pickles",
    ),
    "chile habanero": (
        "salsas, mango, cítricos, cerdo, ceviche",
        "hot sauces, mango, citrus, pork, ceviche",
    ),
    "gochugaru": (
        "kimchi, tofu, guisos coreanos, pollo, fideos",
        "kimchi, tofu, Korean stews, chicken, noodles",
    ),
    "harissa": (
        "cuscús, cordero, verduras asadas, huevos, garbanzos, yogur",
        "couscous, lamb, roast vegetables, eggs, chickpeas, yoghurt",
    ),
    "wasabi": (
        "sushi, atún, salmón, mayonesa, ternera, guisantes",
        "sushi, tuna, salmon, mayonnaise, beef, peas",
    ),
    "rábano picante": (
        "rosbif, salmón ahumado, remolacha, salsas de nata, huevos",
        "roast beef, smoked salmon, beetroot, cream sauces, eggs",
    ),
    # --- Pimentones ---
    "pimentón dulce": (
        "patatas bravas, pulpo, chorizo, lentejas, huevos, sofritos",
        "patatas bravas, octopus, chorizo, lentils, eggs, sofritos",
    ),
    "pimentón picante": (
        "chorizo, patatas, marisco, legumbres, salsas",
        "chorizo, potatoes, seafood, pulses, sauces",
    ),
    "pimentón agridulce": (
        "guisos de cerdo, adobos, legumbres, carnes a la brasa",
        "pork stews, marinades, pulses, grilled meat",
    ),
    "pimentón de la vera": (
        "pulpo a la gallega, chorizo, huevos, patatas, alubias, escabeches",
        "Galician octopus, chorizo, eggs, potatoes, beans, escabeche",
    ),
    "pimentón de murcia": (
        "arroces, morcilla, sofritos, salazones, ensaladas",
        "rice dishes, black pudding, sofritos, salt-cured fish, salads",
    ),
    # --- Mezclas ---
    "curry en polvo": (
        "pollo, lentejas, coliflor, arroz, huevos, calabaza",
        "chicken, lentils, cauliflower, rice, eggs, pumpkin",
    ),
    "garam masala": (
        "curry, cordero, garbanzos, arroz, verduras, yogur",
        "curry, lamb, chickpeas, rice, vegetables, yoghurt",
    ),
    "ras el hanout": (
        "tajín, cuscús, cordero, pollo, zanahoria, calabaza",
        "tagine, couscous, lamb, chicken, carrot, pumpkin",
    ),
    "cinco especias chinas": (
        "cerdo asado, pato, costillas, tofu, salteados",
        "roast pork, duck, ribs, tofu, stir-fries",
    ),
    "hierbas provenzales": (
        "pollo asado, tomate, verduras a la parrilla, pescado, patatas",
        "roast chicken, tomato, grilled vegetables, fish, potatoes",
    ),
    "za'atar": (
        "pan de pita, labneh, pollo, verduras asadas, huevos, aceite",
        "pita bread, labneh, chicken, roast vegetables, eggs, oil",
    ),
    "baharat": (
        "cordero, kebabs, arroz, lentejas, tomate, pollo",
        "lamb, kebabs, rice, lentils, tomato, chicken",
    ),
    "tandoori masala": (
        "pollo, pescado, paneer, yogur, verduras al horno",
        "chicken, fish, paneer, yoghurt, roast vegetables",
    ),
    "shichimi togarashi": (
        "fideos, arroz, edamame, pollo, sopas, huevos",
        "noodles, rice, edamame, chicken, soups, eggs",
    ),
    "chile en polvo": (
        "chili con carne, tacos, frijoles, maíz, pollo",
        "chili con carne, tacos, beans, corn, chicken",
    ),
    "cajún": (
        "gambas, pollo, jambalaya, patatas, pescado, maíz",
        "prawns, chicken, jambalaya, potatoes, fish, corn",
    ),
    "jerk": (
        "pollo, cerdo, pescado, boniato, plátano macho",
        "chicken, pork, fish, sweet potato, plantain",
    ),
    "adobo para pinchitos": (
        "pinchitos de cordero, pollo, cerdo, verduras a la brasa",
        "lamb skewers, chicken, pork, grilled vegetables",
    ),
    "adobo para carne y pescado": (
        "cazón en adobo, pollo, cerdo, boquerones, patatas",
        "dogfish in adobo, chicken, pork, anchovies, potatoes",
    ),
    "mixed spice": (
        "bizcochos, compotas, galletas, pudin, calabaza, manzana",
        "sponges, compotes, biscuits, pudding, pumpkin, apple",
    ),
    "pumpkin spice": (
        "calabaza, tartas, café, galletas, boniato, avena",
        "pumpkin, pies, coffee, biscuits, sweet potato, oats",
    ),
    "quatre épices": (
        "patés, terrinas, cerdo, guisos, pan de especias",
        "pâtés, terrines, pork, stews, spice bread",
    ),
    "dukkah": (
        "pan con aceite, huevos, verduras asadas, ensaladas, cordero",
        "bread and oil, eggs, roast vegetables, salads, lamb",
    ),
    "berberé": (
        "guisos etíopes, lentejas, pollo, ternera, verduras",
        "Ethiopian stews, lentils, chicken, beef, vegetables",
    ),
    "especias para caldereta": (
        "caldereta de cordero, cabrito, guisos de carne, patatas",
        "lamb caldereta, kid goat, meat stews, potatoes",
    ),
    # --- Sales y otros condimentos ---
    "colorante alimentario": (
        "paella, arroces, fideuá, guisos de patatas",
        "paella, rice dishes, fideuá, potato stews",
    ),
    "sal en escamas": (
        "carnes a la brasa, ensaladas, chocolate, pan, tomate, verduras asadas",
        "grilled meat, salads, chocolate, bread, tomato, roast vegetables",
    ),
    "sal ahumada": (
        "carnes, huevos, patatas, verduras a la parrilla, salsas",
        "meat, eggs, potatoes, grilled vegetables, sauces",
    ),
    "sal de apio": (
        "bloody mary, tomate, huevos, ensaladas, pollo",
        "Bloody Mary, tomato, eggs, salads, chicken",
    ),
    "sal de ajo": (
        "pan, patatas, carnes, palomitas, verduras",
        "bread, potatoes, meat, popcorn, vegetables",
    ),
    "ajo en polvo": (
        "adobos, patatas, carnes, salsas, pan, arroz",
        "marinades, potatoes, meat, sauces, bread, rice",
    ),
    "cebolla en polvo": (
        "hamburguesas, salsas, adobos, sopas, arroz",
        "burgers, sauces, marinades, soups, rice",
    ),
    "glutamato": (
        "caldos, ramen, salteados, sopas, carnes",
        "broths, ramen, stir-fries, soups, meat",
    ),
    "alga kombu": (
        "caldo dashi, legumbres, arroz, sopas, pescado",
        "dashi stock, pulses, rice, soups, fish",
    ),
    "alga nori": (
        "sushi, arroz, ramen, ensaladas, tofu, huevos",
        "sushi, rice, ramen, salads, tofu, eggs",
    ),
    "bonito seco": (
        "caldo dashi, tofu, okonomiyaki, arroz, verduras",
        "dashi stock, tofu, okonomiyaki, rice, vegetables",
    ),
    "miso": (
        "sopa, berenjena, salmón, aliños, mantequilla, caramelo",
        "soup, aubergine, salmon, dressings, butter, caramel",
    ),
    "salsa de soja": (
        "arroz, salteados, pescado, tofu, marinadas, carnes",
        "rice, stir-fries, fish, tofu, marinades, meat",
    ),
    "salsa de pescado": (
        "curry tailandés, pad thai, ensaladas, marinadas, sopas",
        "Thai curry, pad thai, salads, marinades, soups",
    ),
    "tamarindo": (
        "pad thai, chutneys, curry, pescado, bebidas, lentejas",
        "pad thai, chutneys, curry, fish, drinks, lentils",
    ),
    "cáscara de cítricos seca": (
        "guisos, repostería, té, arroz, pescado, pato",
        "stews, baking, tea, rice, fish, duck",
    ),
    "amchur": (
        "chutneys, curry, samosas, legumbres, ensaladas",
        "chutneys, curry, samosas, pulses, salads",
    ),
    "asafétida": (
        "lentejas, curry de verduras, patatas, encurtidos, arroz",
        "lentils, vegetable curry, potatoes, pickles, rice",
    ),
}
