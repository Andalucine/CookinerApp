/** The six kinds of note (session 9), in the order the picker shows them, with their icon.
 * A note without a kind shows the notebook page icon. No React Native here (tested with Node). */
import type { TextKey } from "../i18n/translate.ts";
import type { NoteKind } from "./notes.ts";

export const NOTE_KINDS: { code: NoteKind; label: TextKey; icon: string }[] = [
  { code: "recipes", label: "noteKind.recipes", icon: "book-outline" },
  { code: "wines", label: "noteKind.wines", icon: "wine-outline" },
  { code: "spices", label: "noteKind.spices", icon: "leaf-outline" },
  { code: "celebrations", label: "noteKind.celebrations", icon: "gift-outline" },
  { code: "shopping", label: "noteKind.shopping", icon: "cart-outline" },
  { code: "ideas", label: "noteKind.ideas", icon: "bulb-outline" },
];

export const NO_KIND_ICON = "document-text-outline";

export function kindIcon(kind: NoteKind | null | undefined): string {
  return NOTE_KINDS.find((k) => k.code === kind)?.icon ?? NO_KIND_ICON;
}

export function kindLabel(kind: NoteKind | null | undefined): TextKey | null {
  return NOTE_KINDS.find((k) => k.code === kind)?.label ?? null;
}

/** Tapping the chosen kind again leaves the note without a kind. */
export function toggleKind(current: NoteKind | null, tapped: NoteKind): NoteKind | null {
  return current === tapped ? null : tapped;
}
