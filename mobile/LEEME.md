# App móvil de CookinerApp

Expo SDK 57 · React Native · Expo Router · TypeScript. Se prueba en el móvil real con **Expo Go**.

## Arrancar en el iPhone (desarrollo)

1. La API tiene que estar en marcha en el Mac: `docker compose up` en la raíz del repositorio.
2. El iPhone y el Mac, en la **misma wifi**. En el iPhone, la app **Expo Go** (App Store).
3. En otra terminal: `cd mobile` → `npm install` (solo la primera vez o cuando cambie `package.json`) → `npx expo start`.
4. Escanear el código QR con la **cámara** del iPhone y abrir con Expo Go.

La app busca la API en el mismo Mac que sirve la app, puerto 8000 (`services/apiUrl.ts`). Para usar otra dirección: `EXPO_PUBLIC_API_URL=https://… npx expo start`.

## Comprobaciones

- `npm test` — tests de la lógica que no depende del teléfono (textos en los dos idiomas, dirección de la API, validaciones, formato de tiempos y cantidades, filtros de búsqueda, árbol de categorías, vídeos de YouTube), con el sistema de tests de Node.
- Las dos comprobaciones se repiten solas en GitHub en cada commit que cambie `mobile/` (`.github/workflows/mobile.yml`).
- `npm run typecheck` — comprobación de tipos de todo el código.

## Estructura

```
app/          Pantallas (Expo Router): (auth)/ entrar, crear cuenta, recuperar contraseña;
              index.tsx inicio con las cinco puertas; una carpeta por sección
              (recipes/: portada, categorías, buscar, lista, ficha [id], nueva receta;
              spices/[id]: ficha de una especia)
components/   Piezas reutilizables y colores (theme.ts)
services/     Llamadas a la API, sesión (token en el llavero del teléfono), validaciones
i18n/         Textos en es/en (nunca escritos en las pantallas)
assets/       Iconos de la app y logotipo (copias optimizadas de Docs/03 - Diseño)
tests/        Tests de Node (`*.test.ts`)
```

Los paquetes se añaden con las versiones compatibles con el SDK (`node_modules/expo/bundledNativeModules.json`); ver la decisión 0006.
