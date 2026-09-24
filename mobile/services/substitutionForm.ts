/**
 * The substitutes of a spice are written one per line: "Comino · 1 : 1 · más suave"
 * (substitute · proportion · note; only the first part is needed). Pure, tested with Node.
 */
import type { Substitution, SubstitutionInput } from "./spices.ts";

const SEPARATOR = /\s*[·|;]\s*/;

export function parseSubstitutionLine(line: string): SubstitutionInput | null {
  const parts = line
    .trim()
    .split(SEPARATOR)
    .map((p) => p.trim());
  const [substitute, ratio, ...rest] = parts;
  if (!substitute) return null;
  return {
    substitute,
    ratio: ratio || null,
    note: rest.join(" · ").trim() || null,
  };
}

export function parseSubstitutionLines(text: string): SubstitutionInput[] {
  return text
    .split(/\r?\n/)
    .map(parseSubstitutionLine)
    .filter((s): s is SubstitutionInput => s !== null);
}

/** The card's substitutes back to lines, to start editing from them. */
export function linesFromSubstitutions(items: Substitution[], language: string): string {
  return items
    .map((s) => {
      const name = language !== "es" ? s.substitute_en : s.substitute_es;
      const note = language !== "es" ? s.note_en : s.note_es;
      return [name, s.ratio ?? "", note ?? ""]
        .join(" · ")
        .replace(/( · )+$/, "");
    })
    .join("\n");
}
