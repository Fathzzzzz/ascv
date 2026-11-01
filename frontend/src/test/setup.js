import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

// jsdom implements neither object URLs nor canvas; components only need the
// former, and the PNG test exercises the pure layout function instead.
if (!URL.createObjectURL) {
  URL.createObjectURL = vi.fn(() => "blob:preview");
}
if (!URL.revokeObjectURL) {
  URL.revokeObjectURL = vi.fn();
}

if (!globalThis.Intl?.Segmenter) {
  // Node 18+ ships Intl.Segmenter; keep a guard for older runtimes.
  console.warn("Intl.Segmenter unavailable: emoji split falls back to code points.");
}
