import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Local-only setup: the dev server proxies /api to the backend on port 8000,
// so the UI uses relative paths and no CORS configuration is needed.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: false,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.js",
    css: false,
  },
});
