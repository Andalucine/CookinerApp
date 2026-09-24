import assert from "node:assert/strict";
import { test } from "node:test";

import { es } from "../i18n/es.ts";
import {
  kindIcon,
  kindLabel,
  NO_KIND_ICON,
  NOTE_KINDS,
  toggleKind,
} from "../services/noteKinds.ts";

test("six kinds, each with its text and its own icon", () => {
  assert.deepEqual(
    NOTE_KINDS.map((k) => k.code),
    ["recipes", "wines", "spices", "celebrations", "shopping", "ideas"],
  );
  for (const k of NOTE_KINDS) assert.ok(es[k.label], k.label);
  assert.equal(new Set(NOTE_KINDS.map((k) => k.icon)).size, 6);
});

test("a note without a kind gets the page icon and no label", () => {
  assert.equal(kindIcon(null), NO_KIND_ICON);
  assert.equal(kindIcon("wines"), "wine-outline");
  assert.equal(kindLabel(null), null);
  assert.equal(kindLabel("shopping"), "noteKind.shopping");
});

test("tapping the chosen kind again removes it", () => {
  assert.equal(toggleKind(null, "ideas"), "ideas");
  assert.equal(toggleKind("ideas", "wines"), "wines");
  assert.equal(toggleKind("wines", "wines"), null);
});
