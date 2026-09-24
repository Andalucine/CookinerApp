/**
 * The ingredients of a blend are written one per line, like in a recipe: "2 cúrcuma",
 * "½ canela (opcional)", "clavo". Pure functions, tested with Node.
 */
import type { BlendInput } from "./spices.ts";

export type BlendLine = { name: string; parts: string; is_optional: boolean };

const OPTIONAL = /\s*\((opcional|optional)\)\s*$/i;
const LEADING_PARTS = /^(\d+\s*[½¼¾⅓⅛]?|[½¼¾⅓⅛]|\d+[.,]\d+|\d+\/\d+)\s+(?:partes?\s+(?:de\s+)?|parts?\s+(?:of\s+)?)?/i;

/** "2 partes de cúrcuma" → {parts "2", name "cúrcuma"}; "clavo" → parts "1". */
export function parseBlendLine(line: string): BlendLine | null {
  let text = line.trim().replace(/\s+/g, " ");
  if (!text) return null;
  let optional = false;
  if (OPTIONAL.test(text)) {
    optional = true;
    text = text.replace(OPTIONAL, "").trim();
  }
  let parts = "1";
  const head = text.match(LEADING_PARTS);
  if (head) {
    parts = head[1].replace(/\s+/g, "").replace(",", ".");
    text = text.slice(head[0].length).trim();
  }
  text = text.replace(/^de\s+/i, "");
  if (!text || /^[\d½¼¾⅓⅛.,/\s]+$/.test(text)) return null; // a number alone is not a spice
  return { name: text, parts, is_optional: optional };
}

export function parseBlendLines(text: string): BlendLine[] {
  return text
    .split(/\r?\n/)
    .map(parseBlendLine)
    .filter((l): l is BlendLine => l !== null);
}

/** The saved items back to lines, to edit them. */
export function linesFromItems(
  items: { name: string; name_en: string | null; parts: string; is_optional: boolean }[],
  language: string,
  optionalWord: string,
): string {
  return items
    .map((it) => {
      const name = (language === "en" && it.name_en) || it.name;
      return `${it.parts} ${name}${it.is_optional ? ` (${optionalWord})` : ""}`;
    })
    .join("\n");
}

/** What the form checks before saving: a name and at least one ingredient. */
export function blendErrors(
  input: BlendInput,
): { name?: "required"; items?: "required" | "self" } {
  const errors: { name?: "required"; items?: "required" | "self" } = {};
  if (!input.name.trim()) errors.name = "required";
  if (input.items.length === 0) errors.items = "required";
  else if (input.items.some((i) => i.name.toLowerCase() === input.name.trim().toLowerCase())) {
    errors.items = "self";
  }
  return errors;
}
