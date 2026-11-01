import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, convertImage } from "./api.js";

const options = {
  mode: "ascii",
  width: 100,
  charset: "standard",
  invert: false,
  removeBg: true,
};

function okResponse(payload) {
  return { ok: true, status: 200, json: async () => payload };
}

function errorResponse(status, payload) {
  return { ok: false, status, json: async () => payload };
}

describe("convertImage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("posts multipart form data to the relative API path", async () => {
    const fetchImpl = vi.fn(async () => okResponse({ text: "@@", width: 2, height: 1, mode: "ascii" }));
    const file = new File(["abc"], "foto.png", { type: "image/png" });

    const result = await convertImage(file, options, { fetchImpl });

    expect(result.text).toBe("@@");
    const [url, init] = fetchImpl.mock.calls[0];
    expect(url).toBe("/api/convert"); // relative: Vite proxies it
    expect(init.method).toBe("POST");
    expect(init.body).toBeInstanceOf(FormData);
    expect(init.body.get("image").name).toBe("foto.png");
    expect(init.body.get("mode")).toBe("ascii");
    expect(init.body.get("width")).toBe("100");
    expect(init.body.get("remove_bg")).toBe("true");
    expect(init.body.get("invert")).toBe("false");
  });

  it("surfaces the backend detail message on 400", async () => {
    const fetchImpl = vi.fn(async () =>
      errorResponse(400, { detail: "Lebar mode ascii harus antara 40 dan 200 kolom." }),
    );

    await expect(convertImage(new File(["a"], "a.png"), options, { fetchImpl })).rejects.toMatchObject({
      name: "ApiError",
      message: "Lebar mode ascii harus antara 40 dan 200 kolom.",
      status: 400,
    });
  });

  it("uses a size hint when the server returns 413 without a detail", async () => {
    const fetchImpl = vi.fn(async () => ({
      ok: false,
      status: 413,
      json: async () => {
        throw new Error("not json");
      },
    }));

    await expect(convertImage(new File(["a"], "a.png"), options, { fetchImpl })).rejects.toThrow(
      "File terlalu besar (maksimum 5 MB).",
    );
  });

  it("reports an unreachable backend", async () => {
    const fetchImpl = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });

    const failure = convertImage(new File(["a"], "a.png"), options, { fetchImpl });

    await expect(failure).rejects.toBeInstanceOf(ApiError);
    await expect(failure).rejects.toThrow("Backend tidak dapat dihubungi");
  });
});
