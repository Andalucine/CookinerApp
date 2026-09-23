/** Calls to the CookinerApp API: base address, token, language and error messages. */
import Constants from "expo-constants";

import { apiBaseUrl } from "./apiUrl.ts";

export const API_URL = apiBaseUrl(Constants.expoConfig?.hostUri, process.env.EXPO_PUBLIC_API_URL);

/** An error to show to the person: `message` already comes in their language from the API. */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string | null,
  ) {
    super(message ?? "");
  }
}

/** The request never reached the API (no connection, wrong address, API stopped). */
export class NetworkError extends Error {}

type Options = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string | null;
  language?: string;
};

export async function api<T>(path: string, options: Options = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "Accept-Language": options.language ?? "es",
  };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.token) headers.Authorization = `Bearer ${options.token}`;

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new NetworkError();
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    // FastAPI: {"detail": "message"} for our errors, {"detail": [...]} for invalid data
    const detail = data && typeof data.detail === "string" ? data.detail : null;
    throw new ApiError(response.status, detail);
  }
  return data as T;
}
