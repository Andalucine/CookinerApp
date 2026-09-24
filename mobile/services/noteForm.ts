/** The note form without React Native (tested with Node), session 9. */
import type { NoteInput, NoteKind } from "./notes.ts";

export const TITLE_MAX = 200;
const TITLE_FROM_TEXT = 60;

/** What was typed → what is saved. The title may be left empty: then the first line of the
 * text is the title, like the first line of a page in a paper notebook. `null` when there is
 * nothing to save (no title and no text). */
export function toNoteInput(
  title: string,
  text: string,
  kind: NoteKind | null = null,
): NoteInput | null {
  const content = text.replace(/\s+$/, "").replace(/^\s*\n/, "");
  let name = title.trim().replace(/\s+/g, " ");
  if (!name) {
    const first = content.split("\n").find((line) => line.trim()) ?? "";
    name = first.trim().replace(/\s+/g, " ");
    if (name.length > TITLE_FROM_TEXT) {
      const cut = name.slice(0, TITLE_FROM_TEXT - 1);
      name = `${cut.includes(" ") ? cut.slice(0, cut.lastIndexOf(" ")) : cut}…`;
    }
  }
  if (!name) return null;
  return { title: name.slice(0, TITLE_MAX), content: content.trim() ? content : null, kind };
}
