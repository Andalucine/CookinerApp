/** Wines of a notebook (API /wines), the wine catalogue (types and facets) and the wines
 * recommended for a recipe (API /recipes/{id}/wines). */
import { api } from "./apiClient.ts";
import type { Localized } from "./format.ts";
import type { RecipeWines } from "./recipes.ts";
import { toWineQuery, type WineFilters } from "./wineQuery.ts";

type Auth = { token: string; language: string };

export type WineCategoryNode = Localized & {
  id: number;
  slug: string;
  examples_es: string | null;
  serving_temp: string | null;
  children: WineCategoryNode[];
};

export type FacetValue = { code: string; name_es: string; name_en: string };
export type WineFacets = {
  sweetness: FacetValue[];
  body: FacetValue[];
  ageing: FacetValue[];
  price_ranges: string[];
};

export type WineCategoryRef = Localized & {
  id: number;
  slug: string;
  parent: Localized | null;
  serving_temp: string | null;
};

export type WineSummary = {
  id: number;
  notebook_id: number;
  name: string;
  winery: string | null;
  category: WineCategoryRef | null;
  appellation: string | null;
  vintage: number | null;
  price_range: string | null;
  image_url: string | null;
  added_by: string | null;
  is_favorite: boolean;
};

export type Wine = WineSummary & {
  sweetness: string | null;
  body: string | null;
  ageing: string | null;
  country: string | null;
  grapes: string | null;
  tasting_notes: string | null;
  pairing_notes: string | null;
  /** Names of the food categories the pairing rules give for its type (session 8). */
  pairs_with_categories: string[];
  source_url: string | null;
  source_name: string | null;
  source_price: number | null;
  edited_by: string | null;
  created_at: string;
  updated_at: string;
};

/** What is sent to create or replace a wine. */
export type WineInput = {
  name: string;
  winery: string | null;
  category_id: number | null;
  sweetness: string | null;
  body: string | null;
  ageing: string | null;
  country: string | null;
  appellation: string | null;
  grapes: string | null;
  vintage: number | null;
  price_range: string | null;
  tasting_notes: string | null;
  pairing_notes: string | null;
  source_url: string | null;
  source_name: string | null;
  source_price: number | null;
  image_url: string | null;
};

export type WineRecipe = {
  link_id: number;
  recipe_id: number;
  title: string;
  reason: string | null;
  added_by: string | null;
};

export function wineCategories(language: string) {
  return api<WineCategoryNode[]>("/catalog/wine-categories", { language });
}

export function wineFacets(language: string) {
  return api<WineFacets>("/catalog/wine-facets", { language });
}

export function search({ token, language }: Auth, filters: WineFilters, limit = 50, offset = 0) {
  return api<{ total: number; items: WineSummary[] }>(
    `/wines${toWineQuery(filters, { limit, offset })}`,
    { token, language },
  );
}

export function categoryCounts({ token, language }: Auth) {
  return api<{ category_id: number; count: number }[]>("/wines/category-counts", {
    token,
    language,
  });
}

export function get({ token, language }: Auth, id: number) {
  return api<Wine>(`/wines/${id}`, { token, language });
}

export function recipesOf({ token, language }: Auth, id: number) {
  return api<WineRecipe[]>(`/wines/${id}/recipes`, { token, language });
}

export function create({ token, language }: Auth, body: WineInput) {
  return api<Wine>("/wines", { method: "POST", body, token, language });
}

export function update({ token, language }: Auth, id: number, body: WineInput) {
  return api<Wine>(`/wines/${id}`, { method: "PUT", body, token, language });
}

export function remove({ token, language }: Auth, id: number) {
  return api<{ message: string }>(`/wines/${id}`, { method: "DELETE", token, language });
}

export function setFavorite({ token, language }: Auth, id: number, on: boolean) {
  return api<{ message: string }>(`/wines/${id}/favorite`, {
    method: on ? "POST" : "DELETE",
    token,
    language,
  });
}

// --- Wines recommended for a recipe --------------------------------------------------------

export function recommend(
  { token, language }: Auth,
  recipeId: number,
  wineId: number,
  reason: string | null,
) {
  return api<RecipeWines>(`/recipes/${recipeId}/wines`, {
    method: "POST",
    body: { wine_id: wineId, reason },
    token,
    language,
  });
}

export function unrecommend({ token, language }: Auth, recipeId: number, linkId: number) {
  return api<{ message: string }>(`/recipes/${recipeId}/wines/${linkId}`, {
    method: "DELETE",
    token,
    language,
  });
}

// --- Import a wine from a web page (API /imports/wine) ------------------------------------

export type WineImportWarning = "no_product_data" | "no_name" | "no_type" | "no_winery";

export type WineImportPreview = {
  notebook_id: number;
  complete: boolean;
  warnings: WineImportWarning[];
  wine: WineInput;
};

export function readPage({ token, language }: Auth, url: string) {
  return api<WineImportPreview>("/imports/wine", {
    method: "POST",
    body: { url: url.trim() },
    token,
    language,
  });
}
