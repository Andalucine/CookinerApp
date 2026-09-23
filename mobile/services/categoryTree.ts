/** The recipe category tree (Salado · Dulce · Bebidas, up to three levels). Pure, tested. */
import type { Localized } from "./format.ts";

export type CategoryNode = Localized & {
  id: number;
  slug: string;
  level: number;
  examples_es: string | null;
  children: CategoryNode[];
};

/** The category with that id and the path to it from the top (the category included). */
export function findCategory(
  tree: CategoryNode[],
  id: number,
): { node: CategoryNode; path: CategoryNode[] } | null {
  for (const node of tree) {
    if (node.id === id) return { node, path: [node] };
    const found = findCategory(node.children, id);
    if (found) return { node: found.node, path: [node, ...found.path] };
  }
  return null;
}

/** API answer [{category_id, count}] → a lookup; categories without recipes count 0. */
export function countLookup(rows: { category_id: number; count: number }[]) {
  const map = new Map(rows.map((r) => [r.category_id, r.count]));
  return (id: number) => map.get(id) ?? 0;
}
