/**
 * PNG export for the result text.
 *
 * Layout is computed in a pure function so it can be unit tested without a
 * canvas: glyph widths are measured per column, which keeps ASCII and emoji
 * aligned even though emoji are wider than monospace cells.
 */

const FONT_STACK =
  '"DejaVu Sans Mono", "Menlo", "Consolas", monospace, "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji"';

export const PNG_FONT_FAMILY = FONT_STACK;
export const PNG_BACKGROUND = "#ffffff";
export const PNG_FOREGROUND = "#111111";
const LINE_HEIGHT_RATIO = 1.25;

/** Split into user-perceived characters (emoji stay whole). */
export function splitGraphemes(line) {
  if (typeof Intl !== "undefined" && typeof Intl.Segmenter === "function") {
    const segmenter = new Intl.Segmenter("und", { granularity: "grapheme" });
    return Array.from(segmenter.segment(line), (part) => part.segment);
  }
  return Array.from(line);
}

/**
 * Compute canvas geometry for the result text.
 *
 * @param {string[]} lines
 * @param {object} opts
 * @param {number} opts.fontSize
 * @param {number} opts.padding
 * @param {(cluster: string) => number} opts.measure
 * @returns {{width: number, height: number, lineHeight: number,
 *   columnWidths: number[], xOffsets: number[]}}
 */
export function computeLayout(lines, { fontSize, padding, measure }) {
  const rows = Math.max(1, lines.length);
  const lineHeight = Math.ceil(fontSize * LINE_HEIGHT_RATIO);
  const columns = Math.max(1, ...lines.map((line) => splitGraphemes(line).length));
  const columnWidths = new Array(columns).fill(0);

  for (const line of lines) {
    splitGraphemes(line).forEach((cluster, index) => {
      columnWidths[index] = Math.max(columnWidths[index], measure(cluster));
    });
  }
  for (let index = 0; index < columnWidths.length; index += 1) {
    // A blank column still needs room; fall back to one glyph advance.
    if (columnWidths[index] <= 0) columnWidths[index] = measure("M");
  }

  const xOffsets = [];
  let cursor = padding;
  for (const width of columnWidths) {
    xOffsets.push(cursor);
    cursor += width;
  }

  return {
    width: Math.ceil(cursor + padding),
    height: Math.ceil(rows * lineHeight + padding * 2),
    lineHeight,
    columnWidths,
    xOffsets,
  };
}

/** Browser-side measure helper bound to a canvas 2D context. */
export function createMeasurer(ctx, fontSize) {
  const cache = new Map();
  return (cluster) => {
    if (!cache.has(cluster)) {
      cache.set(cluster, ctx.measureText(cluster).width || fontSize / 2);
    }
    return cache.get(cluster);
  };
}

/** Render text to a canvas element (2x scale for crisp output). */
export function renderTextToCanvas(text, { fontSize = 16, padding = 16, scale = 2 } = {}) {
  const lines = text.split("\n");
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  ctx.font = `${fontSize}px ${FONT_STACK}`;
  const measure = createMeasurer(ctx, fontSize);
  const layout = computeLayout(lines, { fontSize, padding, measure });

  canvas.width = Math.ceil(layout.width * scale);
  canvas.height = Math.ceil(layout.height * scale);

  ctx.scale(scale, scale);
  ctx.fillStyle = PNG_BACKGROUND;
  ctx.fillRect(0, 0, layout.width, layout.height);
  ctx.font = `${fontSize}px ${FONT_STACK}`;
  ctx.textBaseline = "top";
  ctx.fillStyle = PNG_FOREGROUND;

  lines.forEach((line, row) => {
    const y = padding + row * layout.lineHeight;
    splitGraphemes(line).forEach((cluster, index) => {
      if (cluster === " ") return;
      ctx.fillText(cluster, layout.xOffsets[index], y);
    });
  });

  return canvas;
}

/** Trigger a browser download for a Blob. */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function downloadText(text, filename = "ascii-art.txt") {
  downloadBlob(new Blob([text], { type: "text/plain;charset=utf-8" }), filename);
}

export function downloadPng(text, filename = "ascii-art.png", options) {
  const canvas = renderTextToCanvas(text, options);
  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      if (blob) downloadBlob(blob, filename);
      resolve(blob);
    }, "image/png");
  });
}
