/** Form checks shared by the access screens. Return a text key, or null when it is fine. */
import type { TextKey } from "../i18n/translate.ts";

export const MIN_PASSWORD = 8;

export function checkEmail(value: string): TextKey | null {
  const v = value.trim();
  if (!v) return "error.required";
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? null : "error.email";
}

export function checkPassword(value: string): TextKey | null {
  if (!value) return "error.required";
  return value.length >= MIN_PASSWORD ? null : "error.password";
}

export function checkRequired(value: string): TextKey | null {
  return value.trim() ? null : "error.required";
}

export function checkCode(value: string): TextKey | null {
  return /^\d{6}$/.test(value.trim()) ? null : "error.code";
}
