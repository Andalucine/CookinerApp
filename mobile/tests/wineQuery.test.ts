import assert from "node:assert/strict";
import { test } from "node:test";

import { cleanWineFilters, parseVintage, toWineQuery, wineDetails } from "../services/wineQuery.ts";

test("wine filters keep only known keys and build the query", () => {
  const filters = cleanWineFilters({ q: " rioja ", body: "full", junk: "x", favorites: true });
  assert.deepEqual(filters, { q: "rioja", body: "full", favorites: "true" });
  assert.equal(toWineQuery(filters, { limit: 5 }), "?q=rioja&body=full&favorites=true&limit=5");
  assert.equal(toWineQuery({}), "");
});

test("the second line of a wine card skips what is missing", () => {
  assert.equal(
    wineDetails({ winery: "López de Heredia", appellation: "Rioja", vintage: 2012, price_range: "€€€" }),
    "López de Heredia · Rioja · 2012 · €€€",
  );
  assert.equal(wineDetails({ winery: null, appellation: null, vintage: null, price_range: null }), "");
});

test("the vintage is a four-digit year or nothing", () => {
  assert.equal(parseVintage("2012"), 2012);
  assert.equal(parseVintage("  "), null);
  assert.ok(Number.isNaN(parseVintage("hace mucho")));
});
