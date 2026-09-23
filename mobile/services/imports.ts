/** Importar una receta de una web (API /imports): read the page → preview → save. */
import { api } from "./apiClient.ts";
import type { Recipe, RecipeInput } from "./recipes.ts";

export type ImportWarning =
  "no_recipe_data" | "read_from_text" | "no_ingredients" | "no_instructions" | "no_time";

export type ImportPreview = {
  job_id: number;
  notebook_id: number;
  complete: boolean;
  warnings: ImportWarning[];
  recipe: RecipeInput;
};

type Auth = { token: string; language: string };

export function readPage({ token, language }: Auth, url: string) {
  return api<ImportPreview>("/imports/recipe", {
    method: "POST",
    body: { url: url.trim() },
    token,
    language,
  });
}

export function save({ token, language }: Auth, jobId: number, recipe: RecipeInput) {
  return api<Recipe>(`/imports/${jobId}/save`, { method: "POST", body: recipe, token, language });
}
