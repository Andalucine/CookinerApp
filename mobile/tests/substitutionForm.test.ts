import assert from "node:assert/strict";
import { test } from "node:test";

import {
  linesFromSubstitutions,
  parseSubstitutionLine,
  parseSubstitutionLines,
} from "../services/substitutionForm.ts";

test("a line is substitute · proportion · note", () => {
  assert.deepEqual(parseSubstitutionLine("Comino · 1 : 1 · más suave"), {
    substitute: "Comino",
    ratio: "1 : 1",
    note: "más suave",
  });
  assert.deepEqual(parseSubstitutionLine("Alcaravea"), {
    substitute: "Alcaravea",
    ratio: null,
    note: null,
  });
  assert.deepEqual(parseSubstitutionLine("Sésamo + orégano | mitad y mitad"), {
    substitute: "Sésamo + orégano",
    ratio: "mitad y mitad",
    note: null,
  });
  assert.equal(parseSubstitutionLine("   "), null);
});

test("lines round-trip through the card's substitutes", () => {
  const items = [
    {
      substitute_es: "Cúrcuma",
      substitute_en: "Turmeric",
      substitute_id: 3,
      ratio: "1 pizca = ¼ cdta",
      note_es: "Da el color, no el sabor",
      note_en: "Gives the colour, not the flavour",
    },
    { substitute_es: "Azafrán", substitute_en: "Saffron", substitute_id: 4, ratio: null, note_es: null, note_en: null },
  ];
  const es = linesFromSubstitutions(items, "es");
  assert.equal(es, "Cúrcuma · 1 pizca = ¼ cdta · Da el color, no el sabor\nAzafrán");
  assert.deepEqual(parseSubstitutionLines(es), [
    { substitute: "Cúrcuma", ratio: "1 pizca = ¼ cdta", note: "Da el color, no el sabor" },
    { substitute: "Azafrán", ratio: null, note: null },
  ]);
  assert.equal(linesFromSubstitutions(items, "en").split("\n")[1], "Saffron");
});
