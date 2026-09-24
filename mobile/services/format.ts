/**
 * How recipe data is written on screen. Pure functions (no React Native imports) so they can be
 * tested with Node.
 */
import type { Language } from "../i18n/translate.ts";

/** A catalogue item with both names (categories, seasons, occasions, tags...). */
export type Localized = { name_es: string; name_en: string };

/** Catalogue names exist in Spanish and English: the other languages read the English one. */
export function localName(item: Localized, language: Language): string {
  return language === "es" ? item.name_es : item.name_en;
}

/** 45 → "45 min" · 90 → "1 h 30 min" · 120 → "2 h". */
export function formatMinutes(minutes: number | null | undefined): string | null {
  if (minutes == null || minutes <= 0) return null;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (!hours) return `${rest} min`;
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}

/** 0.5 → "½", 1.5 → "1 ½", 2 → "2", 0.3 → "0,3" (decimal comma except in English). */
export function formatQuantity(value: number, language: Language): string {
  const whole = Math.floor(value);
  const fraction = Math.round((value - whole) * 100) / 100;
  const symbols: Record<number, string> = { 0.25: "¼", 0.5: "½", 0.75: "¾" };
  if (fraction === 0) return String(whole);
  if (symbols[fraction]) return whole ? `${whole} ${symbols[fraction]}` : symbols[fraction];
  const text = String(Math.round(value * 100) / 100);
  return language === "en" ? text : text.replace(".", ",");
}

export type IngredientLine = {
  name: string;
  quantity: number | null;
  unit: string | null;
  raw_text: string | null;
};

/**
 * The line as the person reads it. The text copied from a web page ("300 g de lentejas
 * pardinas") wins; otherwise quantity, unit and name ("600 g bonito", "4 patata").
 */
export function ingredientText(line: IngredientLine, language: Language): string {
  if (line.raw_text?.trim()) return line.raw_text.trim();
  const parts = [
    line.quantity != null ? formatQuantity(line.quantity, language) : null,
    line.unit?.trim() || null,
    line.name,
  ];
  return parts.filter(Boolean).join(" ");
}

/** The steps, one per line; numbers written by hand ("1.", "2)", "Paso 3:") are removed. */
export function splitSteps(instructions: string | null | undefined): string[] {
  if (!instructions) return [];
  return instructions
    .split(/\r?\n/)
    .map((line) => line.trim().replace(/^(paso\s*)?\d+\s*[.):-]\s*/i, ""))
    .filter((line) => line.length > 0);
}

/** The 11-character video id of any usual YouTube address, or null. */
export function youtubeId(url: string | null | undefined): string | null {
  if (!url) return null;
  const patterns = [
    /youtu\.be\/([\w-]{11})/,
    /[?&]v=([\w-]{11})/,
    /youtube(?:-nocookie)?\.com\/(?:embed|shorts|live|v)\/([\w-]{11})/,
  ];
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
}

/** "https://www.directoalpaladar.com/recetas/..." → "directoalpaladar.com". */
export function siteName(url: string | null | undefined): string | null {
  if (!url) return null;
  const match = url.match(/^https?:\/\/(?:www\.)?([^/?#]+)/i);
  return match ? match[1].toLowerCase() : null;
}

/**
 * Who signs the recipe, with the website in brackets when it comes from one (session 7):
 * "Carmen Tía Alia (Directo al Paladar)". Without a cook, the website alone.
 */
export function signature(recipe: {
  cook_name: string | null;
  source_type: string;
  source_name?: string | null;
  source_url?: string | null;
}): string | null {
  const cook = recipe.cook_name?.trim() || null;
  const site =
    recipe.source_type === "web"
      ? recipe.source_name?.trim() || siteName(recipe.source_url) || null
      : null;
  if (cook && site) return `${cook} (${site})`;
  return cook ?? site;
}

/** The time button a recipe belongs to (same limits as the search): up to 30', 30 to 60', more. */
export function timeBucket(minutes: number | null | undefined): "quick" | "medium" | "long" | null {
  if (minutes == null || minutes <= 0) return null;
  if (minutes <= 30) return "quick";
  return minutes <= 60 ? "medium" : "long";
}

/** Minutes written when a time button is chosen and the recipe had none that fitted. */
export const BUCKET_MINUTES = { quick: 30, medium: 60, long: 90 } as const;
