import assert from "node:assert/strict";
import { test } from "node:test";

import { wideFlags } from "../components/gridLayout.ts";

test("two columns; 'Cualquiera' across the top, the four seasons in two rows", () => {
  assert.deepEqual(wideFlags([{ wide: true }, {}, {}, {}, {}]), [true, false, false, false, false]);
});

test("four time buttons: two rows of two", () => {
  assert.deepEqual(wideFlags([{}, {}, {}, {}]), [false, false, false, false]);
});

test("an odd number: the last one takes the whole row", () => {
  assert.deepEqual(wideFlags([{}, {}, {}, {}, {}]), [false, false, false, false, true]);
});
