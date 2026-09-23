import assert from "node:assert/strict";
import { test } from "node:test";

import { en } from "../i18n/en.ts";
import { es } from "../i18n/es.ts";
import { pickLanguage, translate } from "../i18n/translate.ts";

test("Spanish and English have exactly the same texts", () => {
  assert.deepEqual(Object.keys(en).sort(), Object.keys(es).sort());
  for (const [key, text] of Object.entries(en)) assert.ok(text.trim(), `empty English text: ${key}`);
});

test("the same {placeholders} in both languages", () => {
  const names = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
  for (const key of Object.keys(es) as (keyof typeof es)[]) {
    assert.deepEqual(names(en[key]), names(es[key]), key);
  }
});

test("translate fills the placeholders", () => {
  assert.equal(translate("es", "home.greeting", { name: "Beatriz" }), "Hola, Beatriz");
  assert.equal(translate("en", "home.plan", { plan: "Free" }), "Free plan");
  assert.equal(translate("es", "home.greeting"), "Hola, {name}"); // missing value stays visible
});

test("the phone language picks Spanish unless it is English", () => {
  assert.equal(pickLanguage("en"), "en");
  assert.equal(pickLanguage("EN-gb"), "en");
  assert.equal(pickLanguage("ca"), "es");
  assert.equal(pickLanguage(null), "es");
});
