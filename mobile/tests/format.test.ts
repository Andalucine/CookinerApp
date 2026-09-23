import assert from "node:assert/strict";
import { test } from "node:test";

import {
  formatMinutes,
  formatQuantity,
  ingredientText,
  localName,
  signature,
  siteName,
  splitSteps,
  youtubeId,
} from "../services/format.ts";

test("minutes as people say them", () => {
  assert.equal(formatMinutes(45), "45 min");
  assert.equal(formatMinutes(90), "1 h 30 min");
  assert.equal(formatMinutes(120), "2 h");
  assert.equal(formatMinutes(null), null);
  assert.equal(formatMinutes(0), null);
});

test("quantities with fractions and decimal comma", () => {
  assert.equal(formatQuantity(2, "es"), "2");
  assert.equal(formatQuantity(0.5, "es"), "½");
  assert.equal(formatQuantity(1.5, "es"), "1 ½");
  assert.equal(formatQuantity(0.3, "es"), "0,3");
  assert.equal(formatQuantity(0.3, "en"), "0.3");
});

test("ingredient line: the text from the web wins, otherwise quantity, unit and name", () => {
  const base = { name: "lenteja pardina", quantity: 300, unit: "g", raw_text: null };
  assert.equal(ingredientText(base, "es"), "300 g lenteja pardina");
  assert.equal(
    ingredientText({ ...base, raw_text: "300 g de lentejas pardinas" }, "es"),
    "300 g de lentejas pardinas",
  );
  assert.equal(
    ingredientText({ name: "sal", quantity: null, unit: null, raw_text: null }, "es"),
    "sal",
  );
});

test("steps: one per line, without the numbers written by hand", () => {
  assert.deepEqual(splitSteps("1. Sofreír\n\n2) Añadir patatas\nPaso 3: Servir"), [
    "Sofreír",
    "Añadir patatas",
    "Servir",
  ]);
  assert.deepEqual(splitSteps(null), []);
});

test("YouTube video id from the usual addresses", () => {
  const id = "dQw4w9WgXcQ";
  for (const url of [
    `https://www.youtube.com/watch?v=${id}`,
    `https://youtu.be/${id}?t=10`,
    `https://m.youtube.com/watch?feature=share&v=${id}`,
    `https://www.youtube.com/embed/${id}`,
    `https://www.youtube.com/shorts/${id}`,
  ]) {
    assert.equal(youtubeId(url), id, url);
  }
  assert.equal(youtubeId("https://vimeo.com/123"), null);
  assert.equal(youtubeId(null), null);
});

test("site name and localized names", () => {
  assert.equal(siteName("https://www.directoalpaladar.com/recetas/x"), "directoalpaladar.com");
  assert.equal(siteName("no es una web"), null);
  const item = { name_es: "Otoño", name_en: "Autumn" };
  assert.equal(localName(item, "es"), "Otoño");
  assert.equal(localName(item, "en"), "Autumn");
});

test("signature: the cook and, for a web recipe, the website in brackets", () => {
  const web = {
    cook_name: "Carmen Tía Alia",
    source_type: "web",
    source_name: "Directo al Paladar",
    source_url: "https://www.directoalpaladar.com/recetas/x",
  };
  assert.equal(signature(web), "Carmen Tía Alia (Directo al Paladar)");
  assert.equal(signature({ ...web, source_name: null }), "Carmen Tía Alia (directoalpaladar.com)");
  assert.equal(signature({ ...web, cook_name: null }), "Directo al Paladar");
  assert.equal(signature({ cook_name: "abuela Carmen", source_type: "family" }), "abuela Carmen");
  assert.equal(signature({ cook_name: null, source_type: "own" }), null);
});
