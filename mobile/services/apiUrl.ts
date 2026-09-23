/**
 * Where the API is. Pure function (no React Native imports) so it can be tested with Node.
 *
 * In development the phone loads the app from the Mac (Expo shows it as "192.168.1.20:8081"),
 * and the API runs on that same Mac on port 8000. So the API address is the Mac's address with
 * port 8000. EXPO_PUBLIC_API_URL overrides it (for the deployed API, later).
 */
export const API_PORT = 8000;

export function apiBaseUrl(hostUri?: string | null, override?: string | null): string {
  if (override?.trim()) return override.trim().replace(/\/+$/, "");
  const host = hostUri?.split("/")[0]?.split(":")[0];
  return `http://${host || "localhost"}:${API_PORT}`;
}
