/** Pure translation helpers (no React Native imports, so they can be tested with Node). */
import { de } from "./de.ts";
import { en } from "./en.ts";
import { es } from "./es.ts";
import { fr } from "./fr.ts";
import { nl } from "./nl.ts";

export type Language = "es" | "en" | "fr" | "nl" | "de";
export type TextKey = keyof typeof es;

/** The languages of the app, in the order of the selector, each written in its own language. */
export const LANGUAGES: { code: Language; label: string }[] = [
  { code: "es", label: "Español" },
  { code: "en", label: "English" },
  { code: "fr", label: "Français" },
  { code: "nl", label: "Nederlands" },
  { code: "de", label: "Deutsch" },
];

const TEXTS: Record<Language, Record<TextKey, string>> = { es, en, fr, nl, de };

export function isLanguage(code: string): code is Language {
  return LANGUAGES.some((l) => l.code === code);
}

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

/** The phone's language code ("es", "en-GB", "nl", "ca"...) → a language the app has. */
export function pickLanguage(code: string | null | undefined): Language {
  const short = code?.toLowerCase().slice(0, 2) ?? "";
  return isLanguage(short) ? short : "es";
}
