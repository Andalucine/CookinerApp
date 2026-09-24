# App móvil de CookinerApp

Expo SDK 57 · React Native · Expo Router · TypeScript. Se prueba en el móvil real con **Expo Go**.

## Arrancar en el iPhone (desarrollo)

1. La API tiene que estar en marcha en el Mac: `docker compose up` en la raíz del repositorio.
2. El iPhone y el Mac, en la **misma wifi**. En el iPhone, la app **Expo Go** (App Store).
3. En otra terminal: `cd mobile` → `npm install` (solo la primera vez o cuando cambie `package.json`) → `npx expo start`.
4. Escanear el código QR con la **cámara** del iPhone y abrir con Expo Go.

La app busca la API en el mismo Mac que sirve la app, puerto 8000 (`services/apiUrl.ts`). Para usar otra dirección: `EXPO_PUBLIC_API_URL=https://… npx expo start`.

## Comprobaciones

- `npm test` — tests de la lógica que no depende del teléfono (textos en los cinco idiomas, dirección de la API, validaciones, formato de tiempos y cantidades, filtros de búsqueda, árbol de categorías, vídeos de YouTube, cuaderno ajeno, códigos de invitación, formulario y tipos de notas, despensa y lista de la compra, semanas del menú, reglas de equivalencia, líneas de una mezcla y de los sustitutos, filtros de vinos), con el sistema de tests de Node.
- Las dos comprobaciones se repiten solas en GitHub en cada commit que cambie `mobile/` (`.github/workflows/mobile.yml`).
- `npm run typecheck` — comprobación de tipos de todo el código.

## Estructura

```
app/          Pantallas (Expo Router): (auth)/ entrar, crear cuenta, recuperar contraseña;
              index.tsx inicio con las cinco puertas; una carpeta por sección
              (recipes/: portada, categorías, buscar, lista, ficha [id], nueva receta;
              spices/: portada con buscador y familias, list, rules, blend (mezcla),
              spice (especia propia), substitutions (sustitutos propios) y ficha [id];
              wines/: portada, categories (tipos), search, list, ficha [id] con «Comprar en
              Vinoselección» y recommend (vino para una receta); notes/: portada con buscador, ficha [id] y
              write (nueva y editar); pantry/: mi despensa en tres bloques y cook
              (¿qué puedo cocinar?); shopping-list/: lista de la compra por secciones;
              menu/: menú de la semana, setup (prepararlo) y pick (elegir receta para un plato);
              share/: compartir mi cuaderno;
              join/: unirme a un cuaderno; settings/: mi cuenta)
components/   Piezas reutilizables y colores (theme.ts)
services/     Llamadas a la API, sesión (token en el llavero del teléfono), validaciones
i18n/         Textos en es/en/fr/nl/de (nunca escritos en las pantallas)
assets/       Iconos de la app y logotipo (copias optimizadas de Docs/03 - Diseño)
tests/        Tests de Node (`*.test.ts`)
```

## Cuaderno ajeno (sesión 8)

No hay un "cuaderno activo". Cuando se abre el cuaderno de otra persona (desde Mi cuenta o justo después de unirse), las pantallas de recetas y de notas (sesión 9) reciben tres parámetros: `notebook_id`, `notebook_owner` y `notebook_role`. Los lee `services/sharedNotebook.ts`, que también los pasa a la pantalla siguiente. `notebook_id` es además el filtro que usa la API. Sin esos parámetros, la pantalla muestra el cuaderno propio.

## Fotos (sesión 9)

Las fotos se hacen con la cámara o se eligen de la galería (`expo-image-picker`, en `components/Photo.tsx`) y se mandan a la API (`POST /photos`) con el envío de archivos del propio teléfono (`expo-file-system/legacy`, `uploadAsync`), que devuelve una dirección relativa (`/photos/….jpg`) que se guarda en el `image_url` de la receta, el producto de la despensa o la línea de la compra. `services/photos.ts` completa esa dirección con la de la API al mostrarla. En desarrollo los archivos quedan en la carpeta `uploads/` del proyecto, en el Mac.

Los paquetes se añaden con las versiones compatibles con el SDK (`node_modules/expo/bundledNativeModules.json`); ver la decisión 0006.
