/** Access: register, sign in, current user and password recovery (API /auth). */
import type { Language } from "../i18n/translate.ts";
import { api } from "./apiClient.ts";

export type Plan = "free" | "individual" | "family";

export type User = {
  id: number;
  email: string;
  display_name: string;
  language: Language;
  plan: Plan;
  max_recipes: number | null;
  max_shared_with: number | null;
  notebook_id: number;
};

type TokenResponse = { access_token: string; user: User };

export function login(email: string, password: string, language: string) {
  return api<TokenResponse>("/auth/login", {
    method: "POST",
    body: { email: email.trim(), password },
    language,
  });
}

export function register(
  email: string,
  displayName: string,
  password: string,
  language: Language,
) {
  return api<TokenResponse>("/auth/register", {
    method: "POST",
    body: { email: email.trim(), display_name: displayName.trim(), password, language },
    language,
  });
}

export function me(token: string, language: string) {
  return api<User>("/auth/me", { token, language });
}

export function forgotPassword(email: string, language: string) {
  return api<{ message: string }>("/auth/forgot-password", {
    method: "POST",
    body: { email: email.trim() },
    language,
  });
}

export function resetPassword(email: string, code: string, newPassword: string, language: string) {
  return api<{ message: string }>("/auth/reset-password", {
    method: "POST",
    body: { email: email.trim(), code: code.trim(), new_password: newPassword },
    language,
  });
}
