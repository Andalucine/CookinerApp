/** Menú semanal (API /menus), session 9. Always the person's own notebook. */
import { api } from "./apiClient.ts";
import type { RecipeSummary } from "./recipes.ts";
import type { MissingIngredient, ShoppingItem } from "./shopping.ts";

type Auth = { token: string; language: string };

export type Meal = "breakfast" | "lunch" | "dinner";
export type Slot = {
  id: number;
  day: number; // 0 = Monday
  meal: Meal;
  recipe: RecipeSummary | null;
  note: string | null;
};
export type Menu = {
  id: number;
  week_start: string; // "2026-09-28"
  meals: Meal[];
  wants: string | null;
  slots: Slot[];
  notices: string[];
};
export type MenuCheck = {
  week_start: string;
  season: string;
  total_recipes: number;
  breakfast_recipes: number;
  main_recipes: number;
};

export function check({ token, language }: Auth, weekStart: string) {
  return api<MenuCheck>(`/menus/check?week_start=${weekStart}`, { token, language });
}

export function get({ token, language }: Auth, weekStart: string) {
  return api<Menu>(`/menus?week_start=${weekStart}`, { token, language });
}

export function draft(
  { token, language }: Auth,
  weekStart: string,
  meals: Meal[],
  wants: string | null,
) {
  return api<Menu>("/menus/draft", {
    method: "POST",
    body: { week_start: weekStart, meals, wants },
    token,
    language,
  });
}

export function setSlot(
  { token, language }: Auth,
  menuId: number,
  slotId: number,
  input: { recipe_id: number | null; note: string | null },
) {
  return api<Slot>(`/menus/${menuId}/slots/${slotId}`, {
    method: "PUT",
    body: input,
    token,
    language,
  });
}

export function another({ token, language }: Auth, menuId: number, slotId: number) {
  return api<Slot>(`/menus/${menuId}/slots/${slotId}/another`, {
    method: "POST",
    token,
    language,
  });
}

/** Before adding: every ingredient of the week's recipes, once, with what it is for me. */
export function missingForWeek({ token, language }: Auth, menuId: number) {
  return api<MissingIngredient[]>(`/menus/${menuId}/shopping`, { token, language });
}

export function shopping({ token, language }: Auth, menuId: number, ingredientIds?: number[]) {
  return api<{ added: ShoppingItem[]; recipes: number }>(`/menus/${menuId}/shopping`, {
    method: "POST",
    body: ingredientIds ? { ingredient_ids: ingredientIds } : undefined,
    token,
    language,
  });
}

export function remove({ token, language }: Auth, menuId: number) {
  return api<{ message: string }>(`/menus/${menuId}`, { method: "DELETE", token, language });
}
