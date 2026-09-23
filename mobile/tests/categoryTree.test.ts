import assert from "node:assert/strict";
import { test } from "node:test";

import { type CategoryNode, countLookup, findCategory } from "../services/categoryTree.ts";

const node = (id: number, name: string, children: CategoryNode[] = []): CategoryNode => ({
  id,
  slug: name.toLowerCase(),
  name_es: name,
  name_en: name,
  level: 1,
  examples_es: null,
  children,
});

const tree = [
  node(1, "Salado", [node(2, "Pescados", [node(3, "Guisos de pescado")])]),
  node(4, "Dulce"),
];

test("finds a category and the path to it", () => {
  const found = findCategory(tree, 3);
  assert.equal(found?.node.name_es, "Guisos de pescado");
  assert.deepEqual(
    found?.path.map((n) => n.name_es),
    ["Salado", "Pescados", "Guisos de pescado"],
  );
  assert.equal(findCategory(tree, 99), null);
});

test("counts: categories without recipes are 0", () => {
  const count = countLookup([{ category_id: 3, count: 2 }]);
  assert.equal(count(3), 2);
  assert.equal(count(4), 0);
});
