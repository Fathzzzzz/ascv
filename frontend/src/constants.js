/**
 * UI limits and labels. These mirror backend/app/constants.py; the backend
 * re-validates every value, so this file is a UX hint only.
 */

export const MODES = [
  { value: "ascii", label: "ASCII", minWidth: 40, maxWidth: 200, defaultWidth: 100 },
  { value: "emoji", label: "Emoji", minWidth: 20, maxWidth: 80, defaultWidth: 40 },
];

export const CHARSETS = {
  ascii: [
    { value: "standard", label: "Standard (@%#*+=-:. )" },
    { value: "dense", label: "Dense (70 level)" },
    { value: "blocks", label: "Blocks (█▓▒░)" },
  ],
  emoji: [
    { value: "moon", label: "Bulan (🌑→🌕)" },
    { value: "squares", label: "Kotak (⬛→⬜)" },
  ],
};

export const DEFAULT_CHARSET = { ascii: "standard", emoji: "moon" };

export const MAX_FILE_BYTES = 5 * 1024 * 1024;
export const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
export const ACCEPT = ALLOWED_TYPES.join(",");

export const ZOOM_STEPS = [10, 12, 14, 16, 20, 24];
export const DEFAULT_ZOOM = 14;
