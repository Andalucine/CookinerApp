/** Recipes of a notebook (API /recipes): search, card, favourites, spices and wines. */
import type { Language } from "../i18n/translate.ts";
import { api } from "./apiClient.ts";
import type { Occasion, Season, Tag } from "./catalog.ts";
import type { Localized, Translated } from "./format.ts";
import { type RecipeFilters, toQuery } from "./recipeQuery.ts";

export type SourceType = "own" | "web" | "book" | "family" | "other";
export type Role = "owner" | "editor" | "viewer";

export type RecipeCategory = Localized & { id: number; slug: string; is_primary: boolean };

export type RecipeSummary = {
  id: number;
  notebook_id: number;
  title: string;
  prep_time_minutes: number | null;
  time_label: "quick" | "medium" | "long" | null;
  image_url: string | null;
  cook_name: string | null;
  source_type: SourceType;
  source_name: string | null;
  author: { id: number; display_name: string } | null;
  added_by: string | null;
  primary_category: RecipeCategory | null;
  is_favorite: boolean;
};

export type RecipeIngredient = {
  ingredient_id: number;
  name: string;
  quantity: number | null;
  unit: string | null;
  raw_text: string | null;
  position: number;
};

export type Recipe = RecipeSummary & {
  notebook_owner: string;
  my_role: Role;
  description: string | null;
  instructions: string | null;
  servings: number | null;
  source_url: string | null;
  youtube_url: string | null;
  language: Language;
  ingredients: RecipeIngredient[];
  categories: RecipeCategory[];
  tags: Tag[];
  seasons: Season[];
  occasions: Occasion[];
  created_at: string;
  updated_at: string;
};

/** What is sent to create or replace a recipe (also the import preview). */
export type RecipeInput = {
  title: string;
  description: string | null;
  instructions: string | null;
  prep_time_minutes: number | null;
  servings: number | null;
  cook_name: string | null;
  source_type: SourceType;
  source_name: string | null;
  source_url: string | null;
  youtube_url: string | null;
  image_url: string | null;
  language: Language;
  ingredients: {
    name: string;
    quantity: number | null;
    unit: string | null;
    raw_text: string | null;
  }[];
  category_ids: number[];
  tag_ids: number[];
  season_ids: number[];
  occasion_ids: number[];
};

export type RecipeSpice = {
  ingredient_id: number;
  name: string;
  in_my_pantry: boolean;
  is_blend: boolean;
  substitutions: unknown[];
};

export type WineSummary = {
  id: number;
  name: string;
  winery: string | null;
  appellation: string | null;
  vintage: number | null;
  category: (Localized & { parent: Localized | null; serving_temp: string | null }) | null;
  added_by: string | null;
};

export type RecipeWines = {
  recommended: { id: number; wine: WineSummary; reason: string | null; added_by: string | null }[];
  suggestion: {
    based_on: Localized;
    wine_types: ({
      wine_category: Localized & { parent: Localized | null };
      reason_es: string;
      reason_en: string;
    } & Translated<"reason">)[];
    my_wines: WineSummary[];
  } | null;
};

type Auth = { token: string; language: string };

export function search({ token, language }: Auth, filters: RecipeFilters, limit = 50, offset = 0) {
  return api<{ total: number; items: RecipeSummary[] }>(
    `/recipes${toQuery(filters, { limit, offset })}`,
    { token, language },
  );
}

export function get({ token, language }: Auth, id: number) {
  return api<Recipe>(`/recipes/${id}`, { token, language });
}

export function create({ token, language }: Auth, body: RecipeInput & { notebook_id?: number }) {
  return api<Recipe>("/recipes", { method: "POST", body, token, language });
}

export function update({ token, language }: Auth, id: number, body: RecipeInput) {
  return api<Recipe>(`/recipes/${id}`, { method: "PUT", body, token, language });
}

export function remove({ token, language }: Auth, id: number) {
  return api<{ message: string }>(`/recipes/${id}`, { method: "DELETE", token, language });
}

export function setFavorite({ token, language }: Auth, id: number, on: boolean) {
  return api<{ message: string }>(`/recipes/${id}/favorite`, {
    method: on ? "POST" : "DELETE",
    token,
    language,
  });
}

export function spices({ token, language }: Auth, id: number) {
  return api<RecipeSpice[]>(`/recipes/${id}/spices`, { token, language });
}

export function wines({ token, language }: Auth, id: number) {
  return api<RecipeWines>(`/recipes/${id}/wines`, { token, language });
}

export function categoryCounts({ token, language }: Auth, notebookId?: number) {
  const query = notebookId ? `?notebook_id=${notebookId}` : "";
  return api<{ category_id: number; count: number }[]>(`/recipes/category-counts${query}`, {
    token,
    language,
  });
}
