/**
 * The filters of the wine search, travelling from Buscar (or Por tipos) to the list and from
 * the list to the API. The keys are the API's own parameter names. Pure, tested with Node.
 */
export const WINE_FILTER_KEYS = [
  "q",
  "category_id",
  "sweetness",
  "body",
  "ageing",
  "country",
  "appellation",
  "grape",
  "price_range",
  "favorites",
] as const;

export type WineFilterKey = (typeof WINE_FILTER_KEYS)[number];
export type WineFilters = Partial<Record<WineFilterKey, string>>;

export function cleanWineFilters(params: Record<string, unknown>): WineFilters {
  const filters: WineFilters = {};
  for (const key of WINE_FILTER_KEYS) {
    const raw = params[key];
    const value = Array.isArray(raw) ? raw[0] : raw;
    if (typeof value === "string" && value.trim()) filters[key] = value.trim();
    else if (typeof value === "number") filters[key] = String(value);
    else if (value === true) filters[key] = "true";
  }
  return filters;
}

export function toWineQuery(filters: WineFilters, page: { limit?: number; offset?: number } = {}) {
  const parts: string[] = [];
  for (const key of WINE_FILTER_KEYS) {
    const value = filters[key];
    if (value) parts.push(`${key}=${encodeURIComponent(value)}`);
  }
  if (page.limit) parts.push(`limit=${page.limit}`);
  if (page.offset) parts.push(`offset=${page.offset}`);
  return parts.length ? `?${parts.join("&")}` : "";
}

/** "Viña Tondonia · López de Heredia · 2012" — the second line of a wine card. */
export function wineDetails(wine: {
  winery: string | null;
  appellation: string | null;
  vintage: number | null;
  price_range: string | null;
}): string {
  return [wine.winery, wine.appellation, wine.vintage ? String(wine.vintage) : null, wine.price_range]
    .filter((x): x is string => !!x)
    .join(" · ");
}

/** "2012" → 2012; "" → null; "hace mucho" → NaN (the form shows an error). */
export function parseVintage(text: string): number | null {
  const clean = text.trim();
  if (!clean) return null;
  return /^\d{4}$/.test(clean) ? Number(clean) : Number.NaN;
}
