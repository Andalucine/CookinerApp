/** Notas of a notebook (API /notes): free pages with a title and a text (session 9). */
import { api } from "./apiClient.ts";

type Auth = { token: string; language: string };

/** What a note is about (session 9); the same values as the API. */
export type NoteKind = "recipes" | "wines" | "spices" | "celebrations" | "shopping" | "ideas";

export type NoteSummary = {
  id: number;
  notebook_id: number;
  title: string;
  kind: NoteKind | null;
  author_id: number | null;
  preview: string | null; // the first 140 characters of the text
  added_by: string | null; // name, when someone else wrote it in the owner's notebook
  edited_by: string | null;
  updated_at: string;
};

export type Note = NoteSummary & { content: string | null; created_at: string };

export type NoteInput = { title: string; content: string | null; kind: NoteKind | null };

/** The notes of my notebook (or of someone else's, with its id), last changed first. */
export function list({ token, language }: Auth, notebookId?: number, q?: string) {
  const params = new URLSearchParams();
  if (notebookId) params.set("notebook_id", String(notebookId));
  if (q?.trim()) params.set("q", q.trim());
  const query = params.toString();
  return api<NoteSummary[]>(`/notes${query ? `?${query}` : ""}`, { token, language });
}

export function get({ token, language }: Auth, id: number) {
  return api<Note>(`/notes/${id}`, { token, language });
}

export function create({ token, language }: Auth, input: NoteInput, notebookId?: number) {
  const body = notebookId ? { ...input, notebook_id: notebookId } : input;
  return api<Note>("/notes", { method: "POST", body, token, language });
}

export function update({ token, language }: Auth, id: number, input: NoteInput) {
  return api<Note>(`/notes/${id}`, { method: "PUT", body: input, token, language });
}

export function remove({ token, language }: Auth, id: number) {
  return api<{ message: string }>(`/notes/${id}`, { method: "DELETE", token, language });
}
