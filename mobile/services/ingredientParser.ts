/**
 * Ingredients written by hand, one per line ("300 g de lentejas", "2 dientes de ajo, picados",
 * "sal") → what the API stores: name (to search and to find its spice card), quantity, unit
 * and the line as written. Pure functions, tested with Node.
 */
import type { Language } from "../i18n/translate.ts";
import { type IngredientLine, ingredientText } from "./format.ts";

const UNITS = [
  "g", "gr", "grs", "gramo", "gramos", "kg", "kilo", "kilos", "mg",
  "ml", "cl", "dl", "l", "litro", "litros",
  "cda", "cdas", "cucharada", "cucharadas", "cdta", "cdtas", "cucharadita", "cucharaditas",
  "taza", "tazas", "vaso", "vasos", "diente", "dientes", "pizca", "pizcas",
  "hoja", "hojas", "rama", "ramas", "ramita", "ramitas", "lata", "latas", "sobre", "sobres",
  "unidad", "unidades", "puñado", "puñados", "chorro", "chorrito", "barra", "barras",
  "loncha", "lonchas", "rebanada", "rebanadas", "manojo", "manojos",
  "tbsp", "tsp", "cup", "cups", "oz", "lb", "lbs", "clove", "cloves", "pinch", "slice", "slices",
]; // prettier-ignore

const FRACTIONS: Record<string, number> = {
  "½": 0.5,
  "¼": 0.25,
  "¾": 0.75,
  "⅓": 1 / 3,
  "⅔": 2 / 3,
};

const QUANTITY = String.raw`(\d+\s*[½¼¾⅓⅔]|\d+\s+\d+\/\d+|\d+\/\d+|\d+(?:[.,]\d+)?|[½¼¾⅓⅔])`;
const LINE = new RegExp(
  String.raw`^${QUANTITY}?\s*(?:(${UNITS.join("|")})\.?(?=\s|$))?\s*(?:(?:de|del|of)\s+)?(.*)$`,
  "i",
);

export type IngredientItem = IngredientLine;

function toNumber(text: string): number {
  const t = text.trim();
  const mixedSymbol = t.match(/^(\d+)\s*([½¼¾⅓⅔])$/);
  if (mixedSymbol) return Number(mixedSymbol[1]) + FRACTIONS[mixedSymbol[2]];
  if (FRACTIONS[t] !== undefined) return FRACTIONS[t];
  const mixed = t.match(/^(\d+)\s+(\d+)\/(\d+)$/);
  if (mixed) return Number(mixed[1]) + Number(mixed[2]) / Number(mixed[3]);
  const fraction = t.match(/^(\d+)\/(\d+)$/);
  if (fraction) return Number(fraction[1]) / Number(fraction[2]);
  return Number(t.replace(",", "."));
}

/** The name without what is only preparation: "ajo, picados" → "ajo"; "sal al gusto" → "sal". */
function cleanName(text: string): string {
  return text
    .split(/[,(]/)[0]
    .replace(/\s+(al gusto|to taste|opcional|optional)$/i, "")
    .trim();
}

export function parseIngredientLine(line: string): IngredientItem | null {
  const text = line.trim().replace(/^[-•*·]\s*/, "");
  if (!text) return null;
  const match = text.match(LINE);
  const quantity = match?.[1] ? Math.round(toNumber(match[1]) * 1000) / 1000 : null;
  const unit = match?.[1] && match[2] ? match[2].toLowerCase() : null;
  const rest = match?.[1] ? match[3] : text;
  const name = cleanName(rest || text) || text;
  // Keep the line as written whenever the stored parts would not say the same
  const raw_text = quantity !== null || name !== text ? text : null;
  return { name, quantity, unit, raw_text };
}

/**
 * The text of the ingredients box → the list for the API. A line that was not touched keeps
 * the item it came from (so what the import read stays as it was).
 */
export function linesToIngredients(
  text: string,
  previous: IngredientItem[],
  language: Language,
): IngredientItem[] {
  const byText = new Map(previous.map((item) => [ingredientText(item, language), item]));
  return text
    .split(/\r?\n/)
    .map((line) => byText.get(line.trim()) ?? parseIngredientLine(line))
    .filter((item): item is IngredientItem => item !== null);
}

/** The list → the text of the ingredients box, one per line. */
export function ingredientsToLines(items: IngredientItem[], language: Language): string {
  return items.map((item) => ingredientText(item, language)).join("\n");
}
