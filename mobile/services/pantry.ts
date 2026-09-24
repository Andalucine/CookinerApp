/** Mi despensa (API /pantry): what I have at home, and what I can cook with it (session 9).
 * Always the person's own notebook. */
import { api } from "./apiClient.ts";
import type { RecipeSummary } from "./recipes.ts";

type Auth = { token: string; language: string };

export type Location = "fridge" | "freezer" | "pantry";
export type PantryItem = {
  id: number;
  ingredient_id: number;
  name: string;
  location: Location | null;
};

export type Cookable = {
  recipe: RecipeSummary;
  missing: { ingredient_id: number; name: string }[];
};
export type WhatCanICook = { complete: Cookable[]; missing_one: Cookable[] };

export function get({ token, language }: Auth) {
  return api<{ items: PantryItem[] }>("/pantry", { token, language });
}

export function add({ token, language }: Auth, name: string, location: Location) {
  return api<PantryItem>("/pantry/items", {
    method: "POST",
    body: { name, location },
    token,
    language,
  });
}

export function remove({ token, language }: Auth, id: number) {
  return api<{ message: string }>(`/pantry/items/${id}`, { method: "DELETE", token, language });
}

export function whatCanICook({ token, language }: Auth) {
  return api<WhatCanICook>("/pantry/what-can-i-cook", { token, language });
}
