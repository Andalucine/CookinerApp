/** The spice zone (API /spices, no login): a spice's card with its substitutes. */
import { api } from "./apiClient.ts";

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

export function card(ingredientId: number, language: string) {
  return api<SpiceCard>(`/spices/${ingredientId}`, { language });
}
