/** Lista de la compra (API /shopping-list), grouped by supermarket section (session 9).
 * Always the person's own notebook. */
import { api } from "./apiClient.ts";
import type { Localized } from "./format.ts";

type Auth = { token: string; language: string };

export type ShoppingItem = {
  id: number;
  text: string;
  quantity: string | null;
  ingredient_id: number | null;
  is_checked: boolean;
  recipe_id: number | null;
  image_url: string | null; // a photo of the product (session 9)
};
export type ShoppingSectionGroup = Localized & {
  section_id: number | null;
  code: string;
  items: ShoppingItem[];
};
export type ShoppingList = { sections: ShoppingSectionGroup[]; total: number; pending: number };
export type ShoppingSection = Localized & { id: number; code: string; position: number };

export function get({ token, language }: Auth) {
  return api<ShoppingList>("/shopping-list", { token, language });
}

/** `text` as written ("2 kg de patatas"); `ingredientName` finds its section ("patatas"). */
export function add({ token, language }: Auth, text: string, ingredientName: string) {
  return api<ShoppingItem>("/shopping-list/items", {
    method: "POST",
    body: { text, ingredient_name: ingredientName },
    token,
    language,
  });
}

export function setChecked({ token, language }: Auth, id: number, on: boolean) {
  const path = `/shopping-list/items/${id}/${on ? "check" : "uncheck"}`;
  return api<{ message: string }>(path, { method: "POST", token, language });
}

export function move({ token, language }: Auth, id: number, sectionCode: string) {
  return api<ShoppingItem>(`/shopping-list/items/${id}`, {
    method: "PATCH",
    body: { section_code: sectionCode },
    token,
    language,
  });
}

/** A photo of the product, to buy just that one; null removes it. */
export function setPhoto({ token, language }: Auth, id: number, url: string | null) {
  return api<ShoppingItem>(`/shopping-list/items/${id}`, {
    method: "PATCH",
    body: { image_url: url },
    token,
    language,
  });
}

export function remove({ token, language }: Auth, id: number) {
  return api<{ message: string }>(`/shopping-list/items/${id}`, {
    method: "DELETE",
    token,
    language,
  });
}

/** Remove what was bought; with `toPantry`, it is noted in the pantry first. */
export function clearChecked({ token, language }: Auth, toPantry: boolean) {
  return api<{ message: string }>(`/shopping-list/checked?to_pantry=${toPantry}`, {
    method: "DELETE",
    token,
    language,
  });
}

export type MissingIngredient = {
  ingredient_id: number;
  name: string;
  quantity: string | null;
  recipes: string[];
  status: "missing" | "in_pantry" | "pending" | "staple";
};

/** Before adding: the ingredients of a recipe with what each one is for me (session 9). */
export function missingForRecipe({ token, language }: Auth, recipeId: number) {
  return api<MissingIngredient[]>(`/shopping-list/from-recipe/${recipeId}`, { token, language });
}

/** "Añadir lo que me falta": the ticked ingredients of a recipe (or the missing ones). */
export function fromRecipe({ token, language }: Auth, recipeId: number, ingredientIds?: number[]) {
  return api<ShoppingItem[]>(`/shopping-list/from-recipe/${recipeId}`, {
    method: "POST",
    body: ingredientIds ? { ingredient_ids: ingredientIds } : undefined,
    token,
    language,
  });
}

export function sections(language: string) {
  return api<ShoppingSection[]>("/catalog/shopping-sections", { language });
}
