/** Turn any error from a call into a sentence for the person, in their language. */
import type { TextKey } from "../i18n/translate.ts";
import { ApiError, NetworkError } from "./apiClient.ts";

export function errorText(
  error: unknown,
  t: (key: TextKey, params?: Record<string, string | number>) => string,
): string {
  if (error instanceof NetworkError) return t("error.network");
  if (error instanceof ApiError && error.message) return error.message; // already translated
  return t("error.generic");
}
