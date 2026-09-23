/** Read-only catalogues (API /catalog, no login) and the notebook's occasions (API /occasions). */
import { api } from "./apiClient.ts";
import type { CategoryNode } from "./categoryTree.ts";
import type { Localized } from "./format.ts";

export type CatalogItem = Localized & { id: number };
export type Season = CatalogItem & { code: string };
export type Occasion = CatalogItem & {
  is_preloaded: boolean;
  notebook_id?: number | null;
  added_by?: string | null;
};
export type Tag = CatalogItem & { kind: string; code: string };

export function categories(language: string) {
  return api<CategoryNode[]>("/catalog/categories", { language });
}

export function seasons(language: string) {
  return api<Season[]>("/catalog/seasons", { language });
}

/** Preloaded occasions plus the notebook's own ones. */
export function occasions(token: string, language: string, notebookId?: number) {
  const query = notebookId ? `?notebook_id=${notebookId}` : "";
  return api<Occasion[]>(`/occasions${query}`, { token, language });
}
