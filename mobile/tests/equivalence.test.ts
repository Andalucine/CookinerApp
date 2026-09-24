import assert from "node:assert/strict";
import { test } from "node:test";

import { amountValue, barWidths, readEquivalence, readMeasure } from "../services/equivalence.ts";

test("amounts: whole numbers, fractions, mixed and ranges", () => {
  assert.equal(amountValue("1"), 1);
  assert.equal(amountValue("¾"), 0.75);
  assert.equal(amountValue("1½"), 1.5);
  assert.equal(amountValue("2–3"), 2.5);
  assert.equal(amountValue(""), null);
});

test("a measure is split into amount, label and volume", () => {
  assert.deepEqual(readMeasure("1 cucharada de fresca"), {
    amount: "1",
    label: "cucharada de fresca",
    ml: 15,
  });
  assert.deepEqual(readMeasure("¾ de cucharadita molida"), {
    amount: "¾",
    label: "cucharadita molida",
    ml: 3.75,
  });
  assert.deepEqual(readMeasure("1 diente"), { amount: "1", label: "diente", ml: null });
  assert.deepEqual(readMeasure("1 pizca"), { amount: "1", label: "pizca", ml: 0.6 });
  assert.equal(readMeasure("1 teaspoon dried").ml, 5);
});

test("an equivalence is measures, signs and the ratio in brackets", () => {
  const e = readEquivalence("1 cucharada de fresca = 1 cucharadita de seca (3 : 1)");
  assert.equal(e.ratio, "3 : 1");
  assert.deepEqual(e.signs, ["="]);
  assert.deepEqual(
    e.measures.map((m) => m.label),
    ["cucharada de fresca", "cucharadita de seca"],
  );
});

test("three measures with ≈, and the measures list with ·", () => {
  const chilli = readEquivalence(
    "1 guindilla fresca ≈ ½ cucharadita de copos ≈ ¼ cucharadita de cayena molida",
  );
  assert.equal(chilli.measures.length, 3);
  assert.deepEqual(chilli.signs, ["≈", "≈"]);
  assert.equal(chilli.ratio, null);
  const measures = readEquivalence("1 cucharadita (cdta) = 5 ml · 1 cucharada (cda) = 15 ml");
  assert.deepEqual(measures.signs, ["=", "·", "="]);
});

test("bars are proportional to the volume, only when every volume is known", () => {
  const herbs = readEquivalence("1 cucharada de fresca = 1 cucharadita de seca").measures;
  assert.deepEqual(barWidths(herbs), [1, 5 / 15]);
  const garlic = readEquivalence("1 diente = ¼ cucharadita de ajo en polvo").measures;
  assert.equal(barWidths(garlic), null);
  assert.equal(barWidths([readMeasure("1 pizca")]), null);
});
