import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App.jsx";
import { convertImage } from "./api.js";

vi.mock("./api.js", () => {
  class ApiError extends Error {
    constructor(message, status) {
      super(message);
      this.name = "ApiError";
      this.status = status;
    }
  }
  return { convertImage: vi.fn(), ApiError };
});

const RESULT = {
  text: "@@%%\n..::",
  width: 4,
  height: 2,
  mode: "ascii",
};

function imageFile(name = "foto.png", type = "image/png", bytes = 1024) {
  return new File([new Uint8Array(bytes)], name, { type });
}

async function upload(file) {
  const input = screen.getByLabelText("Pilih gambar");
  // applyAccept: false lets tests feed files the <input accept> would filter.
  await userEvent.upload(input, file, { applyAccept: false });
}

describe("App", () => {
  beforeEach(() => {
    convertImage.mockReset();
    convertImage.mockResolvedValue(RESULT);
    if (!globalThis.URL.revokeObjectURL) URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("starts without a result and disables Convert until a file is chosen", () => {
    render(<App />);

    expect(screen.getByText("Hasil konversi akan muncul di sini.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Convert" })).toBeDisabled();
    expect(screen.getByLabelText(/Lebar \(40–200 kolom\)/)).toHaveValue(100);
  });

  it("converts the uploaded image and renders monospace output", async () => {
    render(<App />);
    await upload(imageFile());

    const convert = screen.getByRole("button", { name: "Convert" });
    expect(convert).toBeEnabled();
    await userEvent.click(convert);

    const pre = await screen.findByTestId("result-text");
    expect(pre.tagName).toBe("PRE");
    expect(pre).toHaveTextContent("@@%%");
    expect(convertImage).toHaveBeenCalledTimes(1);

    const [file, options] = convertImage.mock.calls[0];
    expect(file.name).toBe("foto.png");
    expect(options).toMatchObject({ mode: "ascii", width: 100, charset: "standard", removeBg: true });
    expect(screen.getByText(/ASCII · 4 kolom × 2 baris/)).toBeInTheDocument();
  });

  it("switches mode, width bounds, and charset together", async () => {
    render(<App />);
    await upload(imageFile());

    await userEvent.click(screen.getByRole("radio", { name: "Emoji" }));

    expect(screen.getByLabelText(/Lebar \(20–80 kolom\)/)).toHaveValue(40);
    expect(screen.getByLabelText("Charset")).toHaveValue("moon");

    await userEvent.click(screen.getByRole("button", { name: "Convert" }));
    await screen.findByTestId("result-text");
    expect(convertImage.mock.calls[0][1]).toMatchObject({ mode: "emoji", width: 40, charset: "moon" });
  });

  it("blocks Convert and warns when the width is outside the mode range", async () => {
    render(<App />);
    await upload(imageFile());

    const width = screen.getByLabelText(/Lebar \(40–200 kolom\)/);
    await userEvent.clear(width);
    await userEvent.type(width, "20");

    expect(screen.getByRole("button", { name: "Convert" })).toBeDisabled();
    expect(screen.getByText(/harus antara 40 dan 200 kolom/)).toBeInTheDocument();
  });

  it("shows the backend error message and keeps the result empty", async () => {
    const { ApiError } = await import("./api.js");
    convertImage.mockRejectedValueOnce(new ApiError("Error, blank image", 400));

    render(<App />);
    await upload(imageFile());
    await userEvent.click(screen.getByRole("button", { name: "Convert" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Error, blank image");
    expect(screen.queryByTestId("result-text")).not.toBeInTheDocument();
  });

  it("rejects unsupported files before calling the API", async () => {
    render(<App />);
    await upload(imageFile("catatan.txt", "text/plain"));

    expect(screen.getByRole("alert")).toHaveTextContent("Format harus JPG, PNG, atau WEBP.");
    expect(screen.getByRole("button", { name: "Convert" })).toBeDisabled();
    expect(convertImage).not.toHaveBeenCalled();
  });

  it("rejects files above 5 MB client-side", async () => {
    render(<App />);
    await upload(imageFile("besar.png", "image/png", 5 * 1024 * 1024 + 1));

    expect(screen.getByRole("alert")).toHaveTextContent("Ukuran file maksimum 5 MB.");
    expect(convertImage).not.toHaveBeenCalled();
  });

  it("copies the result to the clipboard", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    render(<App />);
    await upload(imageFile());
    await userEvent.click(screen.getByRole("button", { name: "Convert" }));
    await screen.findByTestId("result-text");

    await userEvent.click(screen.getByRole("button", { name: "Copy teks" }));

    await waitFor(() => expect(writeText).toHaveBeenCalledWith(RESULT.text));
    expect(screen.getByRole("status")).toHaveTextContent("Hasil disalin ke clipboard.");
  });

  it("zooms the result without changing its content", async () => {
    render(<App />);
    await upload(imageFile());
    await userEvent.click(screen.getByRole("button", { name: "Convert" }));
    const pre = await screen.findByTestId("result-text");

    expect(pre).toHaveStyle({ fontSize: "14px" });
    await userEvent.click(screen.getByRole("button", { name: "Perbesar tampilan" }));
    expect(pre).toHaveStyle({ fontSize: "16px" });
    expect(pre).toHaveTextContent("@@%%");
  });

  it("shows a loading indicator while the request is in flight", async () => {
    let resolveRequest;
    convertImage.mockImplementationOnce(
      () => new Promise((resolve) => {
        resolveRequest = resolve;
      }),
    );

    render(<App />);
    await upload(imageFile());
    await userEvent.click(screen.getByRole("button", { name: "Convert" }));

    expect(screen.getByRole("status")).toHaveTextContent("Memproses gambar…");
    expect(screen.getByRole("button", { name: "Memproses…" })).toBeDisabled();

    resolveRequest(RESULT);
    expect(await screen.findByTestId("result-text")).toBeInTheDocument();
  });

  it("accepts a dropped file via drag and drop", async () => {
    render(<App />);

    const zone = screen.getByRole("button", { name: /Area unggah gambar/ });
    const file = imageFile("drop.png");
    const dataTransfer = { files: [file] };

    await userEvent.click(zone); // keyboard/click path should not throw
    fireEvent.drop(zone, { dataTransfer });

    expect(await screen.findByText("drop.png")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Convert" })).toBeEnabled();
  });
});
