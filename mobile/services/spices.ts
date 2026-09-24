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
  // Blends of the notebook (session 8)
  notebook_blend_id: number | null;
  is_own_version: boolean; // the notebook's version of a catalogue blend
  added_by: string | null;
  notebook_spice_id: number | null; // a spice added by the notebook
};

export type OwnSpice = {
  id: number;
  notebook_id: number;
  ingredient_id: number;
  name: string;
  family: string;
  aliases: string | null;
  added_by: string | null;
  created_by_id: number | null;
};

export type OwnSpiceInput = { name: string; family: string; aliases: string | null };
export type SubstitutionInput = { substitute: string; ratio: string | null; note: string | null };

export type BlendItem = {
  ingredient_id: number;
  name: string;
  name_en: string | null;
  parts: string;
  is_optional: boolean;
};

export type Blend = {
  id: number | null; // catalogue row
  notebook_blend_id: number | null; // notebook row
  notebook_id: number | null;
  added_by: string | null;
  created_by_id: number | null;
  ingredient_id: number;
  name: string;
  name_en: string | null;
  note_es: string | null;
  note_en: string | null;
  items: BlendItem[];
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

export type SpiceCard = SpiceSummary & {
  substitutions: Substitution[]; // the notebook's own list when it has one
  has_own_substitutions: boolean;
  substitutions_added_by: string | null;
  blend: Blend | null; // the notebook's version when it has one, else the catalogue's
  catalog_blend: Blend | null; // the catalogue's, only when the notebook has a version
  used_in_blends: { ingredient_id: number; name: string; name_en: string | null }[];
};

/** What is sent to create or replace a blend of the notebook. */
export type BlendInput = {
  name: string;
  note: string | null;
  items: { name: string; parts: string; is_optional: boolean }[];
};

/** The token adds the notebook's own blends; without it the zone is the plain catalogue. */
type Who = { language: string; token?: string | null };

export function families({ language, token }: Who) {
  return api<SpiceFamily[]>("/spices/families", { language, token });
}

/** The spices of a family, or the ones matching a text (name, alias or English name). */
export function list({ language, token }: Who, filter: { family?: string; q?: string }) {
  const parts: string[] = [];
  if (filter.family) parts.push(`family=${encodeURIComponent(filter.family)}`);
  if (filter.q) parts.push(`q=${encodeURIComponent(filter.q)}`);
  return api<SpiceSummary[]>(`/spices${parts.length ? `?${parts.join("&")}` : ""}`, {
    language,
    token,
  });
}

export function rules(language: string) {
  return api<EquivalenceRule[]>("/spices/rules", { language });
}

export function card(ingredientId: number, { language, token }: Who) {
  return api<SpiceCard>(`/spices/${ingredientId}`, { language, token });
}

// --- Blends of my notebook (API /blends) ---------------------------------------------------

type Auth = { token: string; language: string };

export function createBlend({ token, language }: Auth, body: BlendInput) {
  return api<Blend>("/blends", { method: "POST", body, token, language });
}

export function updateBlend({ token, language }: Auth, id: number, body: BlendInput) {
  return api<Blend>(`/blends/${id}`, { method: "PUT", body, token, language });
}

export function removeBlend({ token, language }: Auth, id: number) {
  return api<{ message: string }>(`/blends/${id}`, { method: "DELETE", token, language });
}

// --- Spices and substitute lists of my notebook (API /notebook-spices) ---------------------

export function createSpice({ token, language }: Auth, body: OwnSpiceInput) {
  return api<OwnSpice>("/notebook-spices", { method: "POST", body, token, language });
}

export function updateSpice({ token, language }: Auth, id: number, body: OwnSpiceInput) {
  return api<OwnSpice>(`/notebook-spices/${id}`, { method: "PUT", body, token, language });
}

export function removeSpice({ token, language }: Auth, id: number) {
  return api<{ message: string }>(`/notebook-spices/${id}`, { method: "DELETE", token, language });
}

export function setSubstitutions(
  { token, language }: Auth,
  ingredientId: number,
  items: SubstitutionInput[],
) {
  return api<Substitution[]>(`/notebook-spices/${ingredientId}/substitutions`, {
    method: "PUT",
    body: { items },
    token,
    language,
  });
}

export function clearSubstitutions({ token, language }: Auth, ingredientId: number) {
  return api<{ message: string }>(`/notebook-spices/${ingredientId}/substitutions`, {
    method: "DELETE",
    token,
    language,
  });
}
