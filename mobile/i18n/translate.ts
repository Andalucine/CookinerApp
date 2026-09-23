/** Pure translation helpers (no React Native imports, so they can be tested with Node). */
import { en } from "./en.ts";
import { es } from "./es.ts";

export type Language = "es" | "en";
export type TextKey = keyof typeof es;

const TEXTS: Record<Language, Record<TextKey, string>> = { es, en };

/** "Hola, {name}" + {name: "Ana"} → "Hola, Ana". Unknown language falls back to Spanish. */
export function translate(
  language: Language,
  key: TextKey,
  params: Record<string, string | number> = {},
): string {
  const text = (TEXTS[language] ?? TEXTS.es)[key] ?? TEXTS.es[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in params ? String(params[name]) : match,
  );
}

/** The phone's language code ("es", "en", "ca"...) → a language the app has. */
export function pickLanguage(code: string | null | undefined): Language {
  return code?.toLowerCase().startsWith("en") ? "en" : "es";
}
