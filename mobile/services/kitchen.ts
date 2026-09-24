/** Despensa and lista de la compra without React Native (tested with Node), session 9. */
import { parseIngredientLine } from "./ingredientParser.ts";
import type { Location, PantryItem } from "./pantry.ts";
import type { ShoppingList } from "./shopping.ts";

/** A line typed by hand → what is sent: the line as written and the name that finds its
 * section ("2 kg de patatas" → "patatas"). null for an empty line. */
export function shoppingLine(line: string): { text: string; name: string } | null {
  const text = line.trim().replace(/\s+/g, " ");
  if (!text) return null;
  const parsed = parseIngredientLine(text);
  return { text, name: parsed?.name || text };
}

/** What is typed in the pantry → the ingredient name ("3 limones" → "limones"). */
export function pantryName(line: string): string | null {
  return shoppingLine(line)?.name ?? null;
}

export const LOCATIONS: Location[] = ["fridge", "freezer", "pantry"];

/** The pantry in its three blocks, each in alphabetical order. Without a place → Despensa. */
export function byLocation(items: PantryItem[]): Record<Location, PantryItem[]> {
  const groups: Record<Location, PantryItem[]> = { fridge: [], freezer: [], pantry: [] };
  for (const item of items) groups[item.location ?? "pantry"].push(item);
  for (const place of LOCATIONS) {
    groups[place].sort((a, b) => a.name.localeCompare(b.name, "es"));
  }
  return groups;
}

export function boughtCount(list: ShoppingList): number {
  return list.total - list.pending;
}

/** The list after ticking or unticking one line, before the API answers (so it feels
 * instant). Ticked lines go to the end of their section, as the API orders them. */
export function withChecked(list: ShoppingList, id: number, on: boolean): ShoppingList {
  let changed = 0;
  const sections = list.sections.map((section) => {
    const items = section.items.map((item) => {
      if (item.id !== id || item.is_checked === on) return item;
      changed += 1;
      return { ...item, is_checked: on };
    });
    return {
      ...section,
      items: [...items.filter((i) => !i.is_checked), ...items.filter((i) => i.is_checked)],
    };
  });
  return { ...list, sections, pending: list.pending + (on ? -changed : changed) };
}
