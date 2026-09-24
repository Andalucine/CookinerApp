/**
 * Reads an equivalence rule ("1 cucharada de fresca = 1 cucharadita de seca (3 : 1)") so that
 * the screen can draw it: one tile per measure, the sign between them, and bars proportional
 * to the volume when every measure is a spoon. Pure functions, tested with Node.
 */

export type Measure = {
  amount: string; // "1", "¾", "2–3"…  ("" when the text has no leading number)
  label: string; // "cucharada de fresca"
  ml: number | null; // volume when the unit is known, for the bars
};

export type Equivalence = {
  measures: Measure[];
  signs: string[]; // between measures: "=" or "≈" (or "·" for a plain list)
  ratio: string | null; // "3 : 1" when the text ends with it in brackets
};

const FRACTIONS: Record<string, number> = { "¼": 0.25, "½": 0.5, "¾": 0.75, "⅛": 0.125, "⅓": 1 / 3 };

// Volume of one unit, in ml (Spanish and English spellings, singular and plural)
const UNITS: [RegExp, number][] = [
  [/\b(cucharadita|cdta|teaspoon|tsp)s?\b/i, 5],
  [/\b(cucharada|cda|tablespoon|tbsp)s?\b/i, 15],
  [/\b(pizca|pinch)(es)?\b/i, 0.6],
];

/** "¾" → 0.75, "1" → 1, "2–3" → 2.5, "1½" → 1.5, "" → null. */
export function amountValue(amount: string): number | null {
  const text = amount.trim();
  if (!text) return null;
  const range = text.match(/^(\d+)\s*[–-]\s*(\d+)$/);
  if (range) return (Number(range[1]) + Number(range[2])) / 2;
  let total = 0;
  let matched = false;
  const whole = text.match(/^\d+/);
  if (whole) {
    total += Number(whole[0]);
    matched = true;
  }
  for (const [glyph, value] of Object.entries(FRACTIONS)) {
    if (text.includes(glyph)) {
      total += value;
      matched = true;
    }
  }
  return matched ? total : null;
}

/** "1 cucharada de fresca" → amount "1", label "cucharada de fresca", 15 ml. */
export function readMeasure(text: string): Measure {
  const clean = text.trim().replace(/\s+/g, " ");
  const head = clean.match(/^(\d+\s*[–-]\s*\d+|\d*\s*[¼½¾⅛⅓]|\d+)\s*(de\s+)?/);
  const amount = head ? head[1].replace(/\s+/g, "") : "";
  const label = head ? clean.slice(head[0].length) : clean;
  const value = amountValue(amount);
  let ml: number | null = null;
  if (value !== null) {
    for (const [pattern, unitMl] of UNITS) {
      if (pattern.test(label)) {
        ml = value * unitMl;
        break;
      }
    }
  }
  return { amount, label, ml };
}

/** Splits the whole text into measures and signs; pulls the "(3 : 1)" ratio out. */
export function readEquivalence(text: string): Equivalence {
  let body = text.trim();
  let ratio: string | null = null;
  const tail = body.match(/\(([\d\s:½¼¾]+)\)\s*$/);
  if (tail) {
    ratio = tail[1].trim();
    body = body.slice(0, tail.index).trim();
  }
  const pieces = body.split(/\s*([=≈·])\s*/);
  const measures: Measure[] = [];
  const signs: string[] = [];
  pieces.forEach((piece, index) => {
    if (index % 2 === 0) {
      if (piece.trim()) measures.push(readMeasure(piece));
    } else {
      signs.push(piece);
    }
  });
  return { measures, signs, ratio };
}

/** Bar widths (0–1) proportional to the volume; null when some measure has no known volume. */
export function barWidths(measures: Measure[]): number[] | null {
  if (measures.length < 2 || measures.some((m) => m.ml === null)) return null;
  const max = Math.max(...measures.map((m) => m.ml as number));
  if (max <= 0) return null;
  return measures.map((m) => Math.max(0.06, (m.ml as number) / max));
}
