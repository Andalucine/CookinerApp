import assert from "node:assert/strict";
import { test } from "node:test";

import {
  canAdd,
  canDeleteItem,
  isCompleteCode,
  normalizeCode,
  notebookParams,
  readNotebook,
  shortDate,
} from "../services/sharedNotebook.ts";

test("without notebook parameters the screen shows my own notebook", () => {
  assert.equal(readNotebook({}), null);
  assert.equal(readNotebook({ notebook_id: "7" }), null); // no owner name: not usable
  assert.equal(readNotebook({ notebook_id: "abc", notebook_owner: "Marta" }), null);
});

test("someone else's notebook travels as route parameters and comes back the same", () => {
  const marta = { id: 7, owner: "Marta", role: "editor" as const };
  const params = notebookParams(marta);
  assert.deepEqual(params, { notebook_id: "7", notebook_owner: "Marta", notebook_role: "editor" });
  assert.deepEqual(readNotebook(params), marta);
  assert.deepEqual(notebookParams(null), {});
});

test("an unknown role is read as viewer (the safe side); router arrays are accepted", () => {
  assert.equal(readNotebook({ notebook_id: "7", notebook_owner: "Marta" })?.role, "viewer");
  assert.deepEqual(readNotebook({ notebook_id: ["7"], notebook_owner: ["Marta"] }), {
    id: 7,
    owner: "Marta",
    role: "viewer",
  });
});

test("only the owner (my notebook) and editors see Nueva receta", () => {
  assert.equal(canAdd(null), true);
  assert.equal(canAdd({ id: 7, owner: "Marta", role: "editor" }), true);
  assert.equal(canAdd({ id: 7, owner: "Marta", role: "viewer" }), false);
});

test("the typed code is cleaned: capitals, no spaces or dashes", () => {
  assert.equal(normalizeCode(" k7m2-qxpa "), "K7M2QXPA");
  assert.equal(normalizeCode("K7M2 QXPA"), "K7M2QXPA");
  assert.equal(isCompleteCode("k7m2 qxpa"), true);
  assert.equal(isCompleteCode("K7M2QXP"), false);
  assert.equal(isCompleteCode("K7M2QXPA9"), false);
  assert.equal(isCompleteCode("K7M2QXP!"), false);
});

test("the date of an invitation is short and in words", () => {
  const iso = new Date(2026, 9, 1, 12, 0).toISOString(); // 1 October, local time
  assert.equal(shortDate(iso, "es"), "1 de octubre");
  assert.equal(shortDate(iso, "en"), "1 October");
  assert.equal(shortDate("nonsense", "es"), "");
});

test("only the owner or whoever wrote it can delete", () => {
  const marta = { id: 7, owner: "Marta", role: "editor" as const };
  assert.equal(canDeleteItem(null, 99, 1), true); // my own notebook
  assert.equal(canDeleteItem(marta, 1, 1), true); // I wrote it in Marta's notebook
  assert.equal(canDeleteItem(marta, 99, 1), false);
  assert.equal(canDeleteItem(marta, null, 1), false);
});
