import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, convertImage } from "./api.js";
import { CHARSETS, DEFAULT_CHARSET, MODES } from "./constants.js";
import OptionsPanel from "./components/OptionsPanel.jsx";
import ResultView from "./components/ResultView.jsx";
import UploadDropzone, { validateFile } from "./components/UploadDropzone.jsx";

const DEFAULT_MODE = "ascii";

function initialOptions() {
  const mode = MODES.find((item) => item.value === DEFAULT_MODE);
  return {
    mode: DEFAULT_MODE,
    width: mode.defaultWidth,
    charset: DEFAULT_CHARSET[DEFAULT_MODE],
    invert: false,
    removeBg: true,
  };
}

export default function App() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [options, setOptions] = useState(initialOptions);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const requestRef = useRef(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl("");
      return undefined;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => () => requestRef.current?.abort(), []);

  const handleSelect = useCallback((nextFile) => {
    const message = validateFile(nextFile);
    if (message) {
      setError(message);
      return;
    }
    setError("");
    setResult(null);
    setFile(nextFile);
  }, []);

  async function handleConvert(event) {
    event.preventDefault();
    if (!file || loading) return;

    const message = validateFile(file);
    if (message) {
      setError(message);
      return;
    }

    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;

    setLoading(true);
    setError("");
    try {
      const data = await convertImage(file, options, { signal: controller.signal });
      setResult(data);
    } catch (err) {
      if (err?.name === "AbortError") return;
      setResult(null);
      setError(err instanceof ApiError ? err.message : "Terjadi kesalahan tak terduga.");
    } finally {
      if (requestRef.current === controller) setLoading(false);
    }
  }

  const mode = MODES.find((item) => item.value === options.mode) ?? MODES[0];
  const widthInvalid =
    options.width === "" ||
    !Number.isInteger(options.width) ||
    options.width < mode.minWidth ||
    options.width > mode.maxWidth;
  const canConvert = Boolean(file) && !loading && !widthInvalid;

  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">Image to ASCII/Emoji Converter</h1>
        <p className="app__subtitle">
          Foto dipisahkan dari latar belakang, diubah ke grayscale, lalu dipetakan ke karakter atau
          emoji. Semua proses berjalan lokal.
        </p>
      </header>

      <main className="layout">
        <div className="layout__column">
          <UploadDropzone file={file} onSelect={handleSelect} disabled={loading} />

          {previewUrl ? (
            <section className="panel preview" aria-labelledby="preview-title">
              <h2 id="preview-title" className="panel__title">
                Pratinjau
              </h2>
              <img className="preview__image" src={previewUrl} alt="Pratinjau gambar asli" />
            </section>
          ) : null}

          <form onSubmit={handleConvert} className="form">
            <OptionsPanel options={options} onChange={setOptions} disabled={loading} />

            {widthInvalid ? (
              <p className="hint hint--warning">
                Lebar mode {mode.label} harus antara {mode.minWidth} dan {mode.maxWidth} kolom.
              </p>
            ) : (
              <p className="hint">
                Charset tersedia: {CHARSETS[options.mode].map((item) => item.value).join(", ")}.
              </p>
            )}

            <button type="submit" className="button button--primary" disabled={!canConvert}>
              {loading ? "Memproses…" : result ? "Convert ulang" : "Convert"}
            </button>
          </form>
        </div>

        <div className="layout__column">
          <div aria-live="polite" className="status-region">
            {loading ? (
              <div className="loading" role="status">
                <span className="spinner" aria-hidden="true" />
                <span>Memproses gambar…</span>
              </div>
            ) : null}
            {error ? (
              <p className="alert" role="alert">
                {error}
              </p>
            ) : null}
          </div>

          {result ? (
            <>
              <ResultView result={result} busy={loading} />
              <p className="hint">
                Model segmentasi memuat sekali saat backend start; konversi berikutnya lebih cepat.
              </p>
            </>
          ) : (
            <section className="panel placeholder" aria-label="Belum ada hasil">
              <p>Hasil konversi akan muncul di sini.</p>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
