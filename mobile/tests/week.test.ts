import assert from "node:assert/strict";
import { test } from "node:test";

import type { Slot } from "../services/menu.ts";
import {
  dayName,
  dayOf,
  isThisWeek,
  mondayOf,
  shiftWeek,
  slotsOfDay,
  weekLabel,
  withSlot,
} from "../services/week.ts";

test("the Monday of any day, also of a Sunday and across a month change", () => {
  assert.equal(mondayOf("2026-09-30"), "2026-09-28");
  assert.equal(mondayOf("2026-10-04"), "2026-09-28"); // Sunday belongs to the week before
  assert.equal(mondayOf("2026-09-28"), "2026-09-28");
  assert.equal(mondayOf("2026-11-01"), "2026-10-26");
});

test("weeks before and after, and the days of a week", () => {
  assert.equal(shiftWeek("2026-09-28", 1), "2026-10-05");
  assert.equal(shiftWeek("2026-09-28", -1), "2026-09-21");
  assert.equal(dayOf("2026-09-28", 6), "2026-10-04");
  assert.equal(isThisWeek("2026-09-28", "2026-10-02"), true);
  assert.equal(isThisWeek("2026-09-28", "2026-10-05"), false);
});

test("labels in both languages", () => {
  assert.equal(weekLabel("2026-09-28", "es"), "del 28 de septiembre al 4 de octubre");
  assert.equal(weekLabel("2026-09-28", "en"), "28 September to 4 October");
  assert.equal(weekLabel("2026-09-28", "fr"), "du 28 septembre au 4 octobre");
  assert.equal(weekLabel("2026-09-28", "nl"), "28 september tot 4 oktober");
  assert.equal(weekLabel("2026-09-28", "de"), "28. September bis 4. Oktober");
  assert.equal(dayName(0, "fr"), "Lundi");
  assert.equal(dayName(6, "de"), "Sonntag");
  assert.equal(dayName(0, "es"), "Lunes");
  assert.equal(dayName(6, "en"), "Sunday");
});

test("the slots of a day come in meal order, and one can be replaced", () => {
  const slot = (id: number, day: number, meal: Slot["meal"]): Slot => ({
    id,
    day,
    meal,
    recipe: null,
    note: null,
  });
  const slots = [slot(1, 0, "dinner"), slot(2, 1, "lunch"), slot(3, 0, "breakfast")];
  assert.deepEqual(slotsOfDay(slots, 0).map((s) => s.id), [3, 1]);
  const changed = { ...slot(1, 0, "dinner"), note: "Sobras" };
  assert.equal(withSlot(slots, changed)[0].note, "Sobras");
});
