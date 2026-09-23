/** My notebook (API /notebooks). */
import { api } from "./apiClient.ts";

export type MyNotebook = {
  id: number;
  name: string;
  recipe_count: number;
  shared_with: number;
  max_shared_with: number | null;
};

export function myNotebook(token: string, language: string) {
  return api<MyNotebook>("/notebooks/mine", { token, language });
}
