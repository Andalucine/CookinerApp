/**
 * Sharing a notebook, the parts without React Native (tested with Node):
 * - which notebook a recipe screen is showing: mine, or someone else's opened from its name
 *   (session 8: there is no "active notebook"; the other notebook travels as route parameters);
 * - the invitation code typed by hand;
 * - the short date of an invitation.
 */

export type Role = "viewer" | "editor";

/** Someone else's notebook opened from "Cuadernos compartidos conmigo" or after joining. */
export type OtherNotebook = { id: number; owner: string; role: Role };

/** Route parameters → the other notebook, or null for my own notebook. */
export function readNotebook(params: Record<string, unknown>): OtherNotebook | null {
  const first = (value: unknown) => (Array.isArray(value) ? value[0] : value);
  const id = Number(first(params.notebook_id));
  const owner = first(params.notebook_owner);
  const role = first(params.notebook_role);
  if (!Number.isInteger(id) || id <= 0 || typeof owner !== "string" || !owner.trim()) return null;
  return { id, owner: owner.trim(), role: role === "editor" ? "editor" : "viewer" };
}

/** The other notebook → route parameters to carry it to the next screen (empty for mine). */
export function notebookParams(notebook: OtherNotebook | null): Record<string, string> {
  if (!notebook) return {};
  return {
    notebook_id: String(notebook.id),
    notebook_owner: notebook.owner,
    notebook_role: notebook.role,
  };
}

/** Only the owner and editors add recipes. `null` is my own notebook. */
export function canAdd(notebook: OtherNotebook | null): boolean {
  return notebook === null || notebook.role === "editor";
}

/** Borrar: the owner of the notebook (my own, `null`) or whoever wrote the item (session 9). */
export function canDeleteItem(
  notebook: OtherNotebook | null,
  authorId: number | null,
  myId: number,
): boolean {
  return notebook === null || authorId === myId;
}

export const CODE_LENGTH = 8;

/** What the person typed → the code: capitals, without spaces or dashes (" k7m2-qxpa " →
 * "K7M2QXPA"). Nothing else is guessed: a wrong code gets the API's "no es válido". */
export function normalizeCode(text: string): string {
  return text.replace(/[\s\-_.]/g, "").toUpperCase();
}

export function isCompleteCode(text: string): boolean {
  return /^[A-Z0-9]{8}$/.test(normalizeCode(text));
}

const MONTHS = {
  es: ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
    "octubre", "noviembre", "diciembre"],
  en: ["January", "February", "March", "April", "May", "June", "July", "August", "September",
    "October", "November", "December"],
};

/** "2026-10-01T18:30:00Z" → "1 de octubre" / "1 October" (the phone's local day). */
export function shortDate(iso: string, language: "es" | "en"): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const month = MONTHS[language][date.getMonth()];
  return language === "es" ? `${date.getDate()} de ${month}` : `${date.getDate()} ${month}`;
}
