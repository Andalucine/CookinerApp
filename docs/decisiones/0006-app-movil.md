# 0006 — Base de la app móvil

**Fecha:** 2026-09-23 (sesión 6)

## Contexto
Empieza la app móvil (decisión 0002: Expo / React Native). Se prueba en el iPhone de Beatriz con Expo Go y debe ser fácil de usar para personas con poca soltura digital.

## Decisión
- **Expo SDK 57** (el que acepta Expo Go del App Store en septiembre de 2026), TypeScript estricto, **Expo Router** (una pantalla por archivo en `mobile/app/`).
- **Sesión:** el token de la API se guarda en el almacenamiento seguro del teléfono (`expo-secure-store`, llavero en iPhone); dura 30 días. Al abrir la app, si el token sigue valiendo se entra directamente.
- **Dirección de la API en desarrollo:** la misma máquina que sirve la app en Expo, puerto 8000 (`services/apiUrl.ts`); se puede cambiar con `EXPO_PUBLIC_API_URL` para el despliegue.
- **Idioma:** el del teléfono antes de entrar; el de la cuenta después. Textos en `mobile/i18n/` (es/en), comprobados por un test.
- **Accesibilidad:** textos de 18 pt como base, botones de al menos 56 pt, contraste alto (negro `#090909` sobre blanco, naranja `#FFBE00` del logotipo como único color), etiquetas para VoiceOver.
- **Tests:** la lógica que no depende del teléfono se prueba con el sistema de tests de Node (`npm test`), sin librerías extra; `npm run typecheck` comprueba los tipos.
- **Versiones de paquetes:** las que fija Expo para el SDK (`bundledNativeModules.json`). `react-dom` se fija a la misma versión que `react` para que `npm install` no falle.

## Alternativas descartadas
- `jest-expo`: sus dependencias chocan con las de SDK 57 y harían fallar `npm install`. Se revisará cuando haya que probar pantallas.
- Guardar el token en `AsyncStorage`: no está cifrado.
- Pedir la dirección de la API a mano en el móvil: complica el arranque; se deduce sola.

## Consecuencias
- Las secciones (recetas, vinos…) muestran "Muy pronto" hasta las próximas sesiones.
- La comprobación automática de GitHub todavía no prueba `mobile/` (la carpeta `.github` se edita a mano); pendiente.
