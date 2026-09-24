import assert from "node:assert/strict";
import { test } from "node:test";

import { toNoteInput } from "../services/noteForm.ts";

test("title and text are kept, trimmed", () => {
  assert.deepEqual(toNoteInput("  Pescadería  Manolo ", "Martes y jueves\n\n"), {
    title: "Pescadería Manolo",
    content: "Martes y jueves",
    kind: null,
  });
  assert.equal(toNoteInput("Pescadería", "", "shopping")?.kind, "shopping");
});

test("without a title, the first line of the text is the title", () => {
  assert.deepEqual(toNoteInput("", "\nMenú de Nochebuena\nSopa de marisco"), {
    title: "Menú de Nochebuena",
    content: "Menú de Nochebuena\nSopa de marisco",
    kind: null,
  });
});

test("a long first line is cut at a word, with an ellipsis", () => {
  const long = "Truco para que las lentejas no se peguen nunca aunque las dejes mucho rato al fuego";
  const note = toNoteInput(" ", long);
  assert.ok(note && note.title.endsWith("…") && note.title.length <= 60, note?.title);
  assert.equal(note?.title, "Truco para que las lentejas no se peguen nunca aunque las…");
});

test("a title without text saves an empty text; nothing at all is nothing", () => {
  assert.deepEqual(toNoteInput("Ideas", "   "), { title: "Ideas", content: null, kind: null });
  assert.equal(toNoteInput("  ", " \n "), null);
});
