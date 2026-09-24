import assert from "node:assert/strict";
import { test } from "node:test";

import { byLocation, pantryName, shoppingLine, withChecked } from "../services/kitchen.ts";
import type { ShoppingList } from "../services/shopping.ts";

test("a typed line keeps what was written and finds the ingredient name", () => {
  assert.deepEqual(shoppingLine("  2 kg de  patatas "), {
    text: "2 kg de patatas",
    name: "patatas",
  });
  assert.deepEqual(shoppingLine("leche"), { text: "leche", name: "leche" });
  assert.equal(shoppingLine("   "), null);
  assert.equal(pantryName("3 limones"), "limones");
});

test("the pantry in its three blocks, alphabetical, without a place in Despensa", () => {
  const item = (id: number, name: string, location: "fridge" | "freezer" | "pantry" | null) => ({
    id,
    ingredient_id: id,
    name,
    location,
  });
  const groups = byLocation([
    item(1, "huevo", "fridge"),
    item(2, "arroz", null),
    item(3, "helado", "freezer"),
    item(4, "aceite", "pantry"),
    item(5, "leche", "fridge"),
  ]);
  assert.deepEqual(groups.fridge.map((i) => i.name), ["huevo", "leche"]);
  assert.deepEqual(groups.freezer.map((i) => i.name), ["helado"]);
  assert.deepEqual(groups.pantry.map((i) => i.name), ["aceite", "arroz"]);
});

test("ticking a line moves it to the end of its section and updates what is left", () => {
  const line = (id: number, text: string, is_checked = false) => ({
    id,
    text,
    quantity: null,
    ingredient_id: id,
    is_checked,
    recipe_id: null,
  });
  const list: ShoppingList = {
    sections: [
      {
        section_id: 1,
        code: "produce",
        name_es: "Frutas y verduras",
        name_en: "Fruit & vegetables",
        items: [line(1, "patatas"), line(2, "tomates"), line(3, "ajos", true)],
      },
    ],
    total: 3,
    pending: 2,
  };
  const after = withChecked(list, 1, true);
  assert.deepEqual(after.sections[0].items.map((i) => i.text), ["tomates", "patatas", "ajos"]);
  assert.equal(after.pending, 1);
  assert.equal(withChecked(after, 1, true).pending, 1); // already ticked: nothing changes
  assert.equal(withChecked(after, 3, false).pending, 2);
});
