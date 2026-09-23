/**
 * The filters of the recipe search, travelling from the Buscar screen (or the category tree)
 * to the list, and from the list to the API. The keys are the API's own parameter names.
 * Pure functions, tested with Node.
 */
export const FILTER_KEYS = [
  "q",
  "ingredients",
  "time",
  "max_minutes",
  "cook",
  "source",
  "season_id",
  "occasion_id",
  "category_id",
  "favorites",
  "all_notebooks",
  "notebook_id",
] as const;

export type FilterKey = (typeof FILTER_KEYS)[number];
export type RecipeFilters = Partial<Record<FilterKey, string>>;

/** Keep only known keys with a value (router params can come as arrays or be empty). */
export function cleanFilters(params: Record<string, unknown>): RecipeFilters {
  const filters: RecipeFilters = {};
  for (const key of FILTER_KEYS) {
    const raw = params[key];
    const value = Array.isArray(raw) ? raw[0] : raw;
    if (typeof value === "string" && value.trim()) filters[key] = value.trim();
    else if (typeof value === "number") filters[key] = String(value);
    else if (value === true) filters[key] = "true";
  }
  return filters;
}

export function hasFilters(filters: RecipeFilters): boolean {
  return Object.keys(filters).length > 0;
}

/** "atún, patata y cebolla" → ["atún", "patata", "cebolla"]. */
export function splitIngredients(text: string): string[] {
  return text
    .split(/,|;|\s+y\s+|\s+and\s+/i)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

/** "?ingredients=at%C3%BAn%2Cpatata&limit=50" — the query string for GET /recipes. */
export function toQuery(filters: RecipeFilters, page: { limit?: number; offset?: number } = {}) {
  const parts: string[] = [];
  for (const key of FILTER_KEYS) {
    const value = filters[key];
    if (value) parts.push(`${key}=${encodeURIComponent(value)}`);
  }
  if (page.limit) parts.push(`limit=${page.limit}`);
  if (page.offset) parts.push(`offset=${page.offset}`);
  return parts.length ? `?${parts.join("&")}` : "";
}
