import assert from "node:assert/strict";
import { test } from "node:test";

import {
  blendErrors,
  linesFromItems,
  parseBlendLine,
  parseBlendLines,
} from "../services/blendForm.ts";

test("a line is parts + name, with (opcional) at the end", () => {
  assert.deepEqual(parseBlendLine("2 cúrcuma"), { name: "cúrcuma", parts: "2", is_optional: false });
  assert.deepEqual(parseBlendLine("½ canela (opcional)"), {
    name: "canela",
    parts: "½",
    is_optional: true,
  });
  assert.deepEqual(parseBlendLine("1½ comino"), { name: "comino", parts: "1½", is_optional: false });
  assert.deepEqual(parseBlendLine("2 partes de pimentón dulce"), {
    name: "pimentón dulce",
    parts: "2",
    is_optional: false,
  });
  assert.deepEqual(parseBlendLine("clavo"), { name: "clavo", parts: "1", is_optional: false });
  assert.deepEqual(parseBlendLine("0,5 nuez moscada"), {
    name: "nuez moscada",
    parts: "0.5",
    is_optional: false,
  });
  assert.equal(parseBlendLine("   "), null);
  assert.equal(parseBlendLine("2"), null);
});

test("several lines, empty ones skipped", () => {
  const lines = parseBlendLines("2 cúrcuma\n\n1 comino\n¼ canela (optional)\n");
  assert.deepEqual(
    lines.map((l) => [l.parts, l.name, l.is_optional]),
    [
      ["2", "cúrcuma", false],
      ["1", "comino", false],
      ["¼", "canela", true],
    ],
  );
});

test("saved items go back to lines and parse the same", () => {
  const items = [
    { name: "cúrcuma", name_en: "turmeric", parts: "2", is_optional: false },
    { name: "canela", name_en: "cinnamon", parts: "¼", is_optional: true },
  ];
  const es = linesFromItems(items, "es", "opcional");
  assert.equal(es, "2 cúrcuma\n¼ canela (opcional)");
  assert.deepEqual(
    parseBlendLines(es).map((l) => [l.parts, l.name, l.is_optional]),
    [
      ["2", "cúrcuma", false],
      ["¼", "canela", true],
    ],
  );
  assert.equal(linesFromItems(items, "en", "optional"), "2 turmeric\n¼ cinnamon (optional)");
});

test("the form needs a name and ingredients, and a blend cannot contain itself", () => {
  assert.deepEqual(blendErrors({ name: "", note: null, items: [] }), {
    name: "required",
    items: "required",
  });
  assert.deepEqual(
    blendErrors({
      name: "Curry",
      note: null,
      items: [{ name: "curry", parts: "1", is_optional: false }],
    }),
    { items: "self" },
  );
  assert.deepEqual(
    blendErrors({
      name: "Curry",
      note: null,
      items: [{ name: "cúrcuma", parts: "1", is_optional: false }],
    }),
    {},
  );
});
