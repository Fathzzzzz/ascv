/** Thin client for the local API. Paths are relative; Vite proxies /api to :8000. */

const CONVERT_URL = "/api/convert";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Read `detail` from an error response, falling back to a generic message. */
async function readError(response) {
  const fallback =
    response.status === 413
      ? "File terlalu besar (maksimum 5 MB)."
      : "Gagal memproses gambar.";
  try {
    const body = await response.json();
    if (typeof body?.detail === "string" && body.detail.trim()) {
      return body.detail;
    }
    if (Array.isArray(body?.detail) && body.detail.length > 0) {
      return body.detail.map((item) => item.msg ?? String(item)).join(", ");
    }
  } catch {
    /* non-JSON error body */
  }
  return fallback;
}

/**
 * POST /api/convert with multipart/form-data.
 * @returns {Promise<{text: string, width: number, height: number, mode: string}>}
 */
export async function convertImage(file, options, { signal, fetchImpl = fetch } = {}) {
  const form = new FormData();
  form.append("image", file, file.name);
  form.append("mode", options.mode);
  form.append("width", String(options.width));
  form.append("charset", options.charset);
  form.append("invert", String(Boolean(options.invert)));
  form.append("remove_bg", String(Boolean(options.removeBg)));

  let response;
  try {
    response = await fetchImpl(CONVERT_URL, { method: "POST", body: form, signal });
  } catch (error) {
    if (error?.name === "AbortError") throw error;
    throw new ApiError("Backend tidak dapat dihubungi. Pastikan server berjalan di port 8000.", 0);
  }

  if (!response.ok) {
    throw new ApiError(await readError(response), response.status);
  }
  return response.json();
}
