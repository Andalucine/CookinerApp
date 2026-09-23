import assert from "node:assert/strict";
import { test } from "node:test";

import {
  ingredientsToLines,
  linesToIngredients,
  parseIngredientLine,
} from "../services/ingredientParser.ts";

test("quantity, unit and name from a line written by hand", () => {
  assert.deepEqual(parseIngredientLine("300 g de lentejas pardinas"), {
    name: "lentejas pardinas",
    quantity: 300,
    unit: "g",
    raw_text: "300 g de lentejas pardinas",
  });
  assert.deepEqual(parseIngredientLine("2 dientes de ajo, picados"), {
    name: "ajo",
    quantity: 2,
    unit: "dientes",
    raw_text: "2 dientes de ajo, picados",
  });
  assert.deepEqual(parseIngredientLine("4 patatas"), {
    name: "patatas",
    quantity: 4,
    unit: null,
    raw_text: "4 patatas",
  });
});

test("fractions and decimal comma", () => {
  assert.equal(parseIngredientLine("½ cebolla")?.quantity, 0.5);
  assert.equal(parseIngredientLine("1 ½ tazas de harina")?.quantity, 1.5);
  assert.equal(parseIngredientLine("1/2 limón")?.quantity, 0.5);
  assert.equal(parseIngredientLine("0,5 l de leche")?.quantity, 0.5);
  assert.equal(parseIngredientLine("0,5 l de leche")?.unit, "l");
});

test("lines without quantity", () => {
  assert.deepEqual(parseIngredientLine("sal"), {
    name: "sal",
    quantity: null,
    unit: null,
    raw_text: null,
  });
  assert.deepEqual(parseIngredientLine("- pimienta negra al gusto"), {
    name: "pimienta negra",
    quantity: null,
    unit: null,
    raw_text: "pimienta negra al gusto",
  });
  assert.equal(parseIngredientLine("   "), null);
  // A word that starts like a unit is not a unit: "lechuga" is not "l" + "echuga"
  assert.equal(parseIngredientLine("1 lechuga")?.name, "lechuga");
  assert.equal(parseIngredientLine("1 lechuga")?.unit, null);
});

test("untouched lines keep what the import read", () => {
  const imported = [
    { name: "lenteja pardina", quantity: 300, unit: "g", raw_text: "300 g de lentejas pardinas" },
    { name: "sal", quantity: null, unit: null, raw_text: null },
  ];
  const text = ingredientsToLines(imported, "es");
  assert.equal(text, "300 g de lentejas pardinas\nsal");
  const back = linesToIngredients(`${text}\n1 hoja de laurel\n\n`, imported, "es");
  assert.deepEqual(back[0], imported[0]); // same name as read by the import, not re-parsed
  assert.deepEqual(back[2], {
    name: "laurel",
    quantity: 1,
    unit: "hoja",
    raw_text: "1 hoja de laurel",
  });
  assert.equal(back.length, 3);
});
