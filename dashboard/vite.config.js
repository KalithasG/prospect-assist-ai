import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    // Dev mode: forward API calls to the local demo server so the console
    // shows live data on :5173 too (production serves both from one origin).
    proxy: { "/api": "http://localhost:8000" },
  },
});
