/** My notebook and sharing it (API /notebooks), and the account language (API /auth/me). */
import { api } from "./apiClient.ts";
import type { User } from "./auth.ts";
import type { Role } from "./sharedNotebook.ts";

type Auth = { token: string; language: string };
type Person = { id: number; display_name: string };

export type MyNotebook = {
  id: number;
  name: string;
  owner: Person;
  recipe_count: number;
  shared_with: number;
  max_shared_with: number | null; // null = no limit (family plan)
};

export type Access = { user: Person; role: Role; granted_at: string };

export type Invitation = {
  id: number;
  code: string;
  role: Role;
  invited_email: string | null;
  expires_at: string;
  created_at: string;
};

export type SharedNotebook = {
  id: number;
  name: string;
  owner: Person;
  role: Role;
  granted_at: string;
};

export function mine({ token, language }: Auth) {
  return api<MyNotebook>("/notebooks/mine", { token, language });
}

export function accesses({ token, language }: Auth) {
  return api<Access[]>("/notebooks/mine/access", { token, language });
}

export function changeRole({ token, language }: Auth, userId: number, role: Role) {
  return api<Access>(`/notebooks/mine/access/${userId}`, {
    method: "PATCH",
    body: { role },
    token,
    language,
  });
}

export function removeAccess({ token, language }: Auth, userId: number) {
  return api<{ message: string }>(`/notebooks/mine/access/${userId}`, {
    method: "DELETE",
    token,
    language,
  });
}

export function invitations({ token, language }: Auth) {
  return api<Invitation[]>("/notebooks/mine/invitations", { token, language });
}

export function invite({ token, language }: Auth, role: Role) {
  return api<Invitation>("/notebooks/mine/invitations", {
    method: "POST",
    body: { role },
    token,
    language,
  });
}

export function cancelInvitation({ token, language }: Auth, id: number) {
  return api<{ message: string }>(`/notebooks/mine/invitations/${id}`, {
    method: "DELETE",
    token,
    language,
  });
}

export function join({ token, language }: Auth, code: string) {
  return api<SharedNotebook>("/notebooks/join", {
    method: "POST",
    body: { code },
    token,
    language,
  });
}

export function sharedWithMe({ token, language }: Auth) {
  return api<SharedNotebook[]>("/notebooks/shared-with-me", { token, language });
}

/** Mi cuenta → Idioma. Answers with the updated account. */
export function setLanguage({ token, language }: Auth, newLanguage: "es" | "en") {
  return api<User>("/auth/me", {
    method: "PATCH",
    body: { language: newLanguage },
    token,
    language,
  });
}
