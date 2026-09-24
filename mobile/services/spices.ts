/** The spice zone (API /spices, no login): families, list, equivalence rules and the card of
 * each spice with its substitutes. */
import { api } from "./apiClient.ts";

export type SpiceFamily = { code: string; name_es: string; name_en: string; count: number };

export type SpiceSummary = {
  id: number;
  name: string;
  name_en: string | null;
  aliases: string | null;
  family: string | null;
  has_substitutions: boolean;
  is_blend: boolean;
};

export type EquivalenceRule = {
  id: number;
  situation_es: string;
  situation_en: string;
  equivalence_es: string;
  equivalence_en: string;
  note_es: string | null;
  note_en: string | null;
};

export type Substitution = {
  substitute_es: string;
  substitute_en: string;
  substitute_id: number | null;
  ratio: string | null;
  note_es: string | null;
  note_en: string | null;
};

export type SpiceCard = {
  id: number;
  name: string;
  name_en: string | null;
  aliases: string | null;
  family: string | null;
  is_blend: boolean;
  substitutions: Substitution[];
  blend: {
    items: {
      ingredient_id: number;
      name: string;
      name_en: string | null;
      parts: string;
      is_optional: boolean;
    }[];
    note_es: string | null;
    note_en: string | null;
  } | null;
  used_in_blends: { ingredient_id: number; name: string; name_en: string | null }[];
};

export function families(language: string) {
  return api<SpiceFamily[]>("/spices/families", { language });
}

/** The spices of a family, or the ones matching a text (name, alias or English name). */
export function list(language: string, filter: { family?: string; q?: string }) {
  const parts: string[] = [];
  if (filter.family) parts.push(`family=${encodeURIComponent(filter.family)}`);
  if (filter.q) parts.push(`q=${encodeURIComponent(filter.q)}`);
  return api<SpiceSummary[]>(`/spices${parts.length ? `?${parts.join("&")}` : ""}`, {
    language,
  });
}

export function rules(language: string) {
  return api<EquivalenceRule[]>("/spices/rules", { language });
}

export function card(ingredientId: number, language: string) {
  return api<SpiceCard>(`/spices/${ingredientId}`, { language });
}
