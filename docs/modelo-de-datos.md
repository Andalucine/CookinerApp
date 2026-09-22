# Modelo de datos

Estado: **v2** (migración `initial_schema` regenerada en la sesión 4, decisión 0004: cuaderno personal). Regla: cada cambio en `backend/app/models/` actualiza este documento en el mismo commit. 32 tablas.

## Esquema general

```
users ──< notebooks (1 por cuenta) ──< recipes ──< recipe_ingredients >── ingredients >── shopping_sections
  │            │                          │                                   │
  │            ├─< notebook_access        ├─< recipe_categories >── categories (árbol, 3 niveles)
  │            ├─< notebook_invitations   ├─< recipe_tags >── tags (momento, técnica, dieta, dificultad, origen)
  │            ├─< wines >── wine_categories        ├─< recipe_seasons >── seasons
  │            ├─< notes                  ├─< recipe_occasions >── occasions
  │            ├─< pantry_items           ├─< recipe_contributions
  │            ├─< shopping_list_items    └─< recipe_wines >── wines
  │            └─< import_jobs
  ├─< favorites (receta o vino)
  ├─< auth_identities                     ingredients (especias) ──< spice_substitutions
  └─< password_reset_tokens                                       └─< spice_blends ──< spice_blend_items
                                          spice_equivalence_rules
                                          pairing_rules: categories → wine_categories
```

`A ──< B` significa "un A tiene muchos B". `A >── B` significa que B es un catálogo referenciado.

## Usuarios, plan y acceso

| Tabla | Para qué | Campos clave |
|---|---|---|
| `users` | Cuenta de cada persona | `email` (único), `display_name`, `password_hash` (**nulo** si solo entra con Google/Apple), `language`, `is_active`, `plan` (`free`/`individual`/`family`), `max_recipes` y `max_shared_with` (nulo = sin límite), `family_owner_id` (cuenta que paga el plan familiar) |
| `auth_identities` | Identificación digital: Google, Apple… | `provider`, `provider_user_id` (únicos juntos) |
| `password_reset_tokens` | "He olvidado mi contraseña" | `token_hash`, `expires_at`, `used_at` |

Límites por plan (`PLAN_LIMITS` en `app/models/user.py`): gratuito 15 recetas / comparte con 0; individual sin límite / 2; familiar sin límite / sin límite (5 cuentas).

## Cuaderno

| Tabla | Para qué | Campos clave |
|---|---|---|
| `notebooks` | El cuaderno de una cuenta; se crea al registrarse | `owner_id` (único), `name` ("Cuaderno de Ana") |
| `notebook_access` | Personas con acceso a un cuaderno ajeno | `role`: `viewer` (lector) o `editor`; único por (`notebook_id`, `user_id`). El propietario no tiene fila |
| `notebook_invitations` | Código para entrar en un cuaderno con un rol | `code` (único), `role`, `invited_email`, `expires_at`, `accepted_at` |

## Recetas

| Tabla | Para qué | Campos clave |
|---|---|---|
| `recipes` | La receta | `notebook_id`, `author_id`, `title`, `description`, `instructions`, `prep_time_minutes`, `servings`, `cook_name` ("la abuela"), `source_type` (`own`/`web`/`book`/`family`/`other`), `source_name`, `source_url` (**siempre** si viene de la web), `youtube_url`, `image_url`, `language` |
| `ingredients` | Catálogo **global**, nombre normalizado en minúscula y singular | `name` (único), `name_en`, `aliases`, `is_spice`, `spice_family`, `shopping_section_id` |
| `recipe_ingredients` | Ingredientes de cada receta | `quantity`, `unit`, `raw_text`, `position` |
| `categories` | Árbol de categorías: rama → categoría → subcategoría (`level` 1-3) | `parent_id`, `slug` (único bajo su padre), `name_es`, `name_en`, `examples_es`, `position`, `notebook_id` (nulo = global; preparado para subcategorías propias, no usado en v1) |
| `recipe_categories` | Una receta en varias categorías | `is_primary` (la que se muestra en la ficha) |
| `tags` | Etiquetas cerradas | `kind` (`course`, `method`, `diet`, `difficulty`, `origin`), `code`, `name_es`, `name_en` |
| `recipe_tags` | Etiquetas de cada receta | — |
| `seasons` | Las 4 estaciones | `code`, `name_es`, `name_en` |
| `occasions` | Épocas precargadas (`notebook_id` nulo) o propias del cuaderno | `name_es`, `name_en`, `is_preloaded` |
| `recipe_seasons`, `recipe_occasions` | Varias estaciones y épocas por receta | — |
| `recipe_contributions` | Lo que un editor añadió, para "(añadido por NOMBRE)" | `field`, `content`, `user_id` |

El tiempo (rápida ≤ 30 · media 31–60 · larga > 60) no se guarda: se calcula desde `prep_time_minutes`.

## Especias

| Tabla | Para qué | Campos clave |
|---|---|---|
| `spice_equivalence_rules` | Reglas generales (fresca → seca, entera → molida…) | `situation_*`, `equivalence_*`, `note_*`, `position` |
| `spice_substitutions` | "Si falta X, usa Y" | `ingredient_id` (la que falta), `substitute_es/en` (texto), `substitute_id` (si es un solo ingrediente), `ratio`, `note_es/en` |
| `spice_blends` | Mezclas que se pueden hacer en casa | `ingredient_id` (la mezcla, único), `quick_substitute_*` |
| `spice_blend_items` | Composición de la mezcla | `ingredient_id`, `parts` ("2", "½"), `is_optional` |

## Vinos

| Tabla | Para qué | Campos clave |
|---|---|---|
| `wine_categories` | Árbol de tipos de dos niveles (Tintos → Tinto joven…) | `parent_id`, `slug`, `name_es`, `name_en`, `serving_temp` |
| `wines` | Los vinos **del cuaderno** | `notebook_id`, `added_by_id`, `name`, `winery`, `category_id`, facetas `sweetness`, `body`, `ageing`, `country`, `appellation`, `grapes`, `vintage`, `price_range`, `tasting_notes`, `pairing_notes`, `source_url` |
| `recipe_wines` | Vinos recomendados para una receta **con el motivo** | `reason`, `origin` (`manual`/`imported`) |
| `pairing_rules` | Categoría de receta → tipo de vino, con motivo (sugerencia automática) | `recipe_category_id`, `wine_category_id`, `reason_es/en` |

## Notas, despensa, lista de la compra y favoritos

| Tabla | Para qué | Campos clave |
|---|---|---|
| `notes` | Páginas libres del cuaderno | `title`, `content`, `author_id` |
| `pantry_items` | Lo que hay en casa (sin caducidades) | `ingredient_id` (único por cuaderno), `location` (`fridge`/`freezer`/`pantry`) |
| `shopping_sections` | Secciones del supermercado, en orden de recorrido | `code`, `name_es`, `name_en`, `position` |
| `shopping_list_items` | Líneas de la lista de la compra | `text`, `quantity`, `ingredient_id` (si viene del catálogo), `section_id` (la del ingrediente; "Otros" si no la tiene), `is_checked`, `recipe_id` (de qué receta salió) |
| `favorites` | Estrella en una receta **o** un vino (nunca ambos) | `user_id`, `recipe_id`, `wine_id` |

## Importación

| Tabla | Para qué | Campos clave |
|---|---|---|
| `import_jobs` | Cada intento de importar desde una URL | `kind` (`recipe`/`wine`), `url`, `status`, `error_message`, `recipe_id` o `wine_id` resultante |

## Reglas de negocio que el modelo soporta

- Permisos: sobre un cuaderno, el propietario lo puede todo; `editor` añade y edita recetas (queda en `recipe_contributions`); `viewer` solo ve y puede copiar a su cuaderno o marcar favoritos.
- Límite de recetas del plan gratuito: `users.max_recipes` contra el número de recetas del cuaderno.
- Todo lo importado conserva `source_url`.
- Búsquedas: por ingrediente, tiempo, cocinero (`author_id` o `cook_name`), fuente, estación, época, categoría (incluye subcategorías) y etiquetas.
- "¿Qué puedo cocinar?": recetas cuyos ingredientes están todos en `pantry_items`, o a las que falta uno solo.
- Lista de la compra: la sección la da `ingredients.shopping_section_id`; si no la tiene, "Otros".

## Convenciones

- Todas las tablas tienen `id` entero autoincremental; fechas con zona horaria (`timestamptz`).
- Restricciones con nombre predecible (`pk_`, `fk_tabla_columna_referida`, `uq_tabla_columnas`, `ck_tabla_nombre`, `ix_tabla_columna`), definido en `app/core/database.py`.
- Borrar un cuaderno borra en cascada todo su contenido; los catálogos globales nunca se borran en cascada.
- Borrar una cuenta borra su cuaderno (y todo lo que contiene), sus accesos, favoritos, invitaciones e importaciones; lo que esa persona añadió **en cuadernos ajenos** (recetas, vinos, notas, líneas de la compra, contribuciones) se conserva con el autor a nulo ("añadido por alguien que ya no está"). Preparado para el borrado de cuenta del RGPD, todavía sin endpoint.
- Datos iniciales: `python -m scripts.seed_catalogs` (idempotente).
