import { describe, expect, it } from "vitest";

import { computeLayout, splitGraphemes } from "./png.js";

const fixedMeasurer = (fontSize) => (cluster) => cluster.length * fontSize * 0.6;

describe("splitGraphemes", () => {
  it("keeps emoji such as ZWJ sequences and skin tones intact", () => {
    expect(splitGraphemes("🌑🌕")).toEqual(["🌑", "🌕"]);
    expect(splitGraphemes("👩‍💻")).toEqual(["👩‍💻"]);
    expect(splitGraphemes("👍🏽")).toEqual(["👍🏽"]);
  });

  it("keeps ASCII art cells separate", () => {
    expect(splitGraphemes("@%# .")).toEqual(["@", "%", "#", " ", "."]);
  });
});

describe("computeLayout", () => {
  const measure = fixedMeasurer(16);

  it("sizes the canvas from padding, rows, and column widths", () => {
    const layout = computeLayout(["@@@", "@@@"], { fontSize: 16, padding: 10, measure });

    expect(layout.columnWidths).toHaveLength(3);
    expect(layout.lineHeight).toBe(20); // ceil(16 * 1.25)
    expect(layout.width).toBe(Math.ceil(3 * 9.6 + 20));
    expect(layout.height).toBe(2 * 20 + 20);
  });

  it("uses the widest cell per column so emoji and ASCII stay aligned", () => {
    const layout = computeLayout(["@🌕", "🌕@"], {
      fontSize: 16,
      padding: 0,
      measure: (cluster) => (cluster === "🌕" ? 24 : 9),
    });

    expect(layout.columnWidths).toEqual([24, 24]);
    expect(layout.xOffsets).toEqual([0, 24]);
  });

  it("treats empty lines as blank rows and never collapses to zero size", () => {
    const layout = computeLayout(["", ""], { fontSize: 16, padding: 8, measure });

    expect(layout.columnWidths).toHaveLength(1);
    expect(layout.width).toBeGreaterThan(0);
    expect(layout.height).toBe(2 * 20 + 16);
  });
});
