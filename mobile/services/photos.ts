/** Photos taken with the phone (session 9): sent to the API, which keeps the file and
 * answers with its address; and the address of a photo when it is shown. */
import * as FileSystem from "expo-file-system/legacy";

import { API_URL, ApiError, NetworkError } from "./apiClient.ts";

type Auth = { token: string; language: string };

/** A photo picked or taken with the phone → its address for `image_url`. The upload goes
 * through the phone's own file sender (multipart), which is what works reliably with a
 * file:// address from the camera or the gallery. */
export async function upload({ token, language }: Auth, uri: string, mimeType?: string | null) {
  let result: FileSystem.FileSystemUploadResult;
  try {
    result = await FileSystem.uploadAsync(`${API_URL}/photos`, uri, {
      httpMethod: "POST",
      uploadType: FileSystem.FileSystemUploadType.MULTIPART,
      fieldName: "file",
      mimeType: mimeType || guessType(uri),
      headers: {
        Accept: "application/json",
        "Accept-Language": language,
        Authorization: `Bearer ${token}`,
      },
    });
  } catch {
    throw new NetworkError();
  }
  let data: { url?: string; detail?: unknown } | null = null;
  try {
    data = JSON.parse(result.body);
  } catch {
    data = null;
  }
  if (result.status < 200 || result.status >= 300 || !data?.url) {
    const detail = data && typeof data.detail === "string" ? data.detail : null;
    throw new ApiError(result.status, detail);
  }
  return { url: data.url };
}

function guessType(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase();
  if (ext === "png") return "image/png";
  if (ext === "webp") return "image/webp";
  if (ext === "heic" || ext === "heif") return `image/${ext}`;
  return "image/jpeg";
}

/** "/photos/….jpg" → the full address on the API; a web address stays as it is. */
export function photoUri(url: string | null | undefined): string | null {
  if (!url) return null;
  return url.startsWith("/") ? `${API_URL}${url}` : url;
}
