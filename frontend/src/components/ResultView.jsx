import { useEffect, useState } from "react";

import { DEFAULT_ZOOM, ZOOM_STEPS } from "../constants.js";
import { copyText } from "../lib/clipboard.js";
import { downloadPng, downloadText } from "../lib/png.js";

export default function ResultView({ result, busy }) {
  const [zoom, setZoom] = useState(DEFAULT_ZOOM);
  const [status, setStatus] = useState("");

  useEffect(() => {
    setStatus("");
  }, [result?.text]);

  const fileName = result ? `ascii-art-${result.mode}-${result.width}x${result.height}` : "ascii-art";

  async function handleCopy() {
    const copied = await copyText(result.text);
    setStatus(copied ? "Hasil disalin ke clipboard." : "Clipboard tidak tersedia, salin manual.");
  }

  function handleDownloadTxt() {
    downloadText(result.text, `${fileName}.txt`);
    setStatus("File .txt diunduh.");
  }

  async function handleDownloadPng() {
    try {
      await downloadPng(result.text, `${fileName}.png`, { fontSize: zoom });
      setStatus("File PNG diunduh.");
    } catch {
      setStatus("Export PNG gagal di browser ini.");
    }
  }

  return (
    <section className="panel result" aria-labelledby="result-title">
      <div className="result__header">
        <h2 id="result-title" className="panel__title">
          Hasil
        </h2>
        <div className="zoom" role="group" aria-label="Ukuran tampilan hasil">
          <button
            type="button"
            className="button button--ghost"
            onClick={() => setZoom((value) => Math.max(ZOOM_STEPS[0], value - 2))}
            disabled={zoom <= ZOOM_STEPS[0]}
            aria-label="Perkecil tampilan"
          >
            A−
          </button>
          <span className="zoom__value" aria-live="off">
            {zoom}px
          </span>
          <button
            type="button"
            className="button button--ghost"
            onClick={() =>
              setZoom((value) => Math.min(ZOOM_STEPS[ZOOM_STEPS.length - 1], value + 2))
            }
            disabled={zoom >= ZOOM_STEPS[ZOOM_STEPS.length - 1]}
            aria-label="Perbesar tampilan"
          >
            A+
          </button>
        </div>
      </div>

      <p className="result__meta">
        {result.mode === "emoji" ? "Emoji" : "ASCII"} · {result.width} kolom × {result.height} baris
      </p>

      <pre
        className="result__pre"
        style={{ fontSize: `${zoom}px` }}
        data-testid="result-text"
        aria-label="Hasil konversi"
      >
        {result.text}
      </pre>

      <div className="result__actions">
        <button type="button" className="button" onClick={handleCopy} disabled={busy}>
          Copy teks
        </button>
        <button type="button" className="button" onClick={handleDownloadTxt} disabled={busy}>
          Download .txt
        </button>
        <button type="button" className="button" onClick={handleDownloadPng} disabled={busy}>
          Download PNG
        </button>
      </div>

      {status ? (
        <p className="result__status" role="status">
          {status}
        </p>
      ) : null}
    </section>
  );
}
