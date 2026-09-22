# 0004 — Cuaderno personal en vez de grupos, y una sola migración inicial hasta el despliegue

**Fecha:** 2026-09-22 (sesión 4)  
**Sustituye:** la parte de grupos de la decisión [0003](0003-login-y-acceso.md).

## Contexto
En la sesión 3 se decidió que la unidad de la app es **la cuenta**, no el grupo: cada persona tiene su cuaderno y comparte de forma esporádica con dos roles (lector, editor). El modelo v1 (sesión 2) giraba en torno a `groups` con miembros `admin`/`member`. Además se aprobaron los catálogos (categorías, etiquetas, especias, vinos, secciones de compra) y las zonas nuevas (notas, despensa, lista de la compra, favoritos), que necesitan 14 tablas más.

## Decisión
1. **`groups` desaparece.** Lo sustituye `notebooks`: un cuaderno por cuenta (`owner_id` único), creado automáticamente al registrarse. Recetas, vinos, notas, despensa, lista de la compra, épocas propias e importaciones cuelgan del cuaderno.
2. **Acceso de terceros** en `notebook_access` con `role` = `viewer` | `editor`. El propietario no tiene fila: es el dueño. `notebook_invitations` lleva el rol que concede el código.
3. **Plan en la cuenta**: `users.plan` (`free` | `individual` | `family`) con los límites copiados en la fila (`max_recipes`, `max_shared_with`; nulo = sin límite) para poder hacer excepciones sin cambiar de plan, y `family_owner_id` para agrupar las cinco cuentas de un plan familiar. Los valores por plan están en `PLAN_LIMITS` (`app/models/user.py`): gratuito 15 recetas y 0 compartidos, individual sin límite y 2 compartidos, familiar sin límite.
4. **`recipe_editors` desaparece**: el rol `editor` del cuaderno ya cubre quién puede editar; lo que un editor añade sigue registrándose en `recipe_contributions` para mostrar "(añadido por NOMBRE)".
5. **Los vinos son del cuaderno** (`wines.notebook_id`), igual que las recetas, en lugar de un catálogo global. Lo global son el árbol de tipos (`wine_categories`) y las reglas de maridaje (`pairing_rules`).
6. **Una sola migración inicial hasta el primer despliegue.** La app no tiene datos reales: la migración v1 se ha sustituido por una nueva `initial_schema` con el esquema v2 completo, en vez de escribir una migración de cambio con renombrados y borrados. Quien tenga la base local de la v1 hace `docker compose down -v` y vuelve a aplicar `alembic upgrade head`. **A partir del primer despliegue, cada cambio será una migración incremental** y nunca se volverá a tocar una migración ya aplicada.
7. Los **datos iniciales** (estaciones, épocas, secciones, categorías, etiquetas, especias, sustituciones, mezclas, tipos de vino, reglas de maridaje) salen de la migración y viven en `backend/scripts/seed_catalogs.py`, que se puede ejecutar tantas veces como se quiera sin duplicar.
8. Todas las restricciones de la base de datos llevan **nombre predecible** (convención en `app/core/database.py`), para que las migraciones futuras puedan modificarlas.

## Alternativas descartadas
- Mantener `groups` y tratar el cuaderno como "grupo de una persona": obligaba a crear un grupo por usuario y a arrastrar los roles `admin`/`member`, que no son los del producto.
- Migración de cambio v1 → v2 (renombrar `groups`, mover columnas): más de 300 líneas generadas con restricciones sin nombre y sin datos que preservar; no aportaba nada.
- Guardar los límites solo en código: no permitiría excepciones por cuenta ni cambiar un límite sin desplegar.
- Catálogo global de vinos compartido por todos: complica los permisos y choca con la filosofía del cuaderno personal; se podrá añadir un catálogo de referencia más adelante.

## Consecuencias
- 32 tablas (ver `docs/modelo-de-datos.md`). La comprobación de permisos se hace siempre contra el cuaderno: propietario, editor o lector.
- El registro crea usuario + cuaderno en la misma transacción; los tests lo comprueban.
- Cobro de suscripciones pendiente: `plan` se cambia a mano (o por script) hasta entonces.
