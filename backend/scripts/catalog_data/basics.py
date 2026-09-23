"""Seasons, occasions, shopping sections and tags (closed lists, approved in session 4)."""

SEASONS = [
    ("spring", "Primavera", "Spring"),
    ("summer", "Verano", "Summer"),
    ("autumn", "Otoño", "Autumn"),
    ("winter", "Invierno", "Winter"),
]

# "Verano" was removed in session 7: it is a season, not an occasion.
OCCASIONS = [
    ("Navidad", "Christmas"),
    ("Cuaresma", "Lent"),
    ("Semana Santa", "Easter"),
    ("Feria", "Feria"),
    ("Todos los Santos", "All Saints"),
]

# (code, name_es, name_en) in the order you walk through a supermarket
SHOPPING_SECTIONS = [
    ("produce", "Frutas y verduras", "Fruit & vegetables"),
    ("meat", "Carnes y charcutería", "Meat & deli"),
    ("fish", "Pescados y mariscos", "Fish & seafood"),
    ("dairy", "Lácteos y huevos", "Dairy & eggs"),
    ("bakery", "Pan y bollería", "Bread & bakery"),
    ("grains", "Legumbres, arroz y pasta", "Pulses, rice & pasta"),
    ("pantry", "Conservas y despensa", "Tins & pantry"),
    ("spices", "Especias y condimentos", "Spices & seasonings"),
    ("oils", "Aceites, vinagres y salsas", "Oils, vinegars & sauces"),
    ("frozen", "Congelados", "Frozen"),
    ("drinks", "Bebidas y vinos", "Drinks & wine"),
    ("sweets", "Dulces y repostería", "Sweets & baking"),
    ("other", "Otros", "Other"),
]

# kind -> [(code, name_es, name_en)]
TAGS = {
    "course": [
        ("breakfast", "Desayuno", "Breakfast"),
        ("appetiser", "Aperitivo", "Appetiser"),
        ("starter", "Entrante", "Starter"),
        ("main", "Plato principal", "Main course"),
        ("side", "Guarnición", "Side dish"),
        ("dessert", "Postre", "Dessert"),
        ("snack", "Merienda", "Afternoon snack"),
        ("light-dinner", "Cena ligera", "Light dinner"),
    ],
    "method": [
        ("oven", "Al horno", "Oven-baked"),
        ("griddle", "A la plancha", "Griddled"),
        ("grill", "A la parrilla / barbacoa", "Grilled / barbecue"),
        ("fried", "Frito", "Fried"),
        ("stewed", "Guisado", "Stewed"),
        ("steamed", "Al vapor", "Steamed"),
        ("boiled", "Hervido", "Boiled"),
        ("raw", "Crudo / sin cocción", "Raw / no cooking"),
        ("pressure-cooker", "Olla exprés", "Pressure cooker"),
        ("air-fryer", "Freidora de aire", "Air fryer"),
        ("microwave", "Microondas", "Microwave"),
        ("robot", "Thermomix / robot", "Thermomix / food processor"),
    ],
    "diet": [
        ("vegetarian", "Vegetariana", "Vegetarian"),
        ("vegan", "Vegana", "Vegan"),
        ("gluten-free", "Sin gluten", "Gluten-free"),
        ("lactose-free", "Sin lactosa", "Lactose-free"),
        ("nut-free", "Sin frutos secos", "Nut-free"),
        ("egg-free", "Sin huevo", "Egg-free"),
        ("low-salt", "Baja en sal", "Low salt"),
    ],
    "difficulty": [
        ("easy", "Fácil", "Easy"),
        ("medium", "Media", "Medium"),
        ("hard", "Difícil", "Hard"),
    ],
    # Replaces the "Cocina del mundo" branch of the tree (decision, session 4)
    "origin": [
        ("italian", "Italiana", "Italian"),
        ("french", "Francesa", "French"),
        ("portuguese", "Portuguesa", "Portuguese"),
        ("moroccan-arabic", "Marroquí y árabe", "Moroccan & Arabic"),
        ("mexican-latin", "Mexicana y latinoamericana", "Mexican & Latin American"),
        ("indian", "India", "Indian"),
        ("east-asian", "China, japonesa y del sudeste asiático", "East & Southeast Asian"),
        ("greek-turkish", "Griega y turca", "Greek & Turkish"),
        ("american", "Estadounidense", "American"),
        ("other", "Otras", "Other"),
    ],
}
