import assert from "node:assert/strict";
import { test } from "node:test";

import { cleanFilters, hasFilters, splitIngredients, toQuery } from "../services/recipeQuery.ts";

test("only known filters with a value travel to the list", () => {
  const filters = cleanFilters({
    ingredients: "atún,patata",
    category_id: ["12"],
    title: "Resultados",
    cook: "  ",
    favorites: true,
  });
  assert.deepEqual(filters, { ingredients: "atún,patata", category_id: "12", favorites: "true" });
  assert.equal(hasFilters({}), false);
});

test("ingredients written in any usual way", () => {
  assert.deepEqual(splitIngredients("atún, patata y cebolla"), ["atún", "patata", "cebolla"]);
  assert.deepEqual(splitIngredients(" , "), []);
});

test("query string for the API", () => {
  assert.equal(toQuery({}), "");
  assert.equal(
    toQuery({ ingredients: "atún,patata", time: "quick" }, { limit: 30, offset: 30 }),
    "?ingredients=at%C3%BAn%2Cpatata&time=quick&limit=30&offset=30",
  );
});
