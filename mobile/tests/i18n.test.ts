import assert from "node:assert/strict";
import { test } from "node:test";

import { de } from "../i18n/de.ts";
import { en } from "../i18n/en.ts";
import { es } from "../i18n/es.ts";
import { fr } from "../i18n/fr.ts";
import { nl } from "../i18n/nl.ts";
import { isLanguage, LANGUAGES, pickLanguage, translate } from "../i18n/translate.ts";

const OTHERS: Record<string, Record<string, string>> = { en, fr, nl, de };

test("every language has exactly the same texts as Spanish", () => {
  for (const [code, texts] of Object.entries(OTHERS)) {
    assert.deepEqual(Object.keys(texts).sort(), Object.keys(es).sort(), code);
    for (const [key, text] of Object.entries(texts)) assert.ok(text.trim(), `empty ${code}: ${key}`);
  }
});

test("the same {placeholders} in every language", () => {
  const names = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
  for (const [code, texts] of Object.entries(OTHERS)) {
    for (const key of Object.keys(es) as (keyof typeof es)[]) {
      assert.deepEqual(names(texts[key]), names(es[key]), `${code}: ${key}`);
    }
  }
});

test("translate fills the placeholders in every language", () => {
  assert.equal(translate("es", "home.greeting", { name: "Beatriz" }), "Hola, Beatriz");
  assert.equal(translate("en", "home.plan", { plan: "Free" }), "Free plan");
  assert.equal(translate("fr", "home.greeting", { name: "Marie" }), "Bonjour, Marie");
  assert.equal(translate("nl", "home.greeting", { name: "Anne" }), "Hallo, Anne");
  assert.equal(translate("de", "home.greeting", { name: "Anna" }), "Hallo, Anna");
  assert.equal(translate("es", "home.greeting"), "Hola, {name}"); // missing value stays visible
});

test("the phone language picks one of the five, Spanish otherwise", () => {
  assert.equal(pickLanguage("en"), "en");
  assert.equal(pickLanguage("EN-gb"), "en");
  assert.equal(pickLanguage("fr-BE"), "fr");
  assert.equal(pickLanguage("nl"), "nl");
  assert.equal(pickLanguage("de-AT"), "de");
  assert.equal(pickLanguage("ca"), "es");
  assert.equal(pickLanguage(null), "es");
});

test("the selector lists the five languages, each in its own name", () => {
  assert.deepEqual(
    LANGUAGES.map((l) => l.code),
    ["es", "en", "fr", "nl", "de"],
  );
  assert.ok(isLanguage("nl"));
  assert.ok(!isLanguage("it"));
});
