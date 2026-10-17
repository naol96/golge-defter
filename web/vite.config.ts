import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// The stdlib kokpit server serves index.html at "/" and every other file under
// "/assets/<name>", so production assets live flat in dist/ behind that prefix.
export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === "build" ? "/assets/" : "/",
  build: { outDir: "dist", assetsDir: "", emptyOutDir: true, sourcemap: false },
  server: {
    port: 5173,
    proxy: { "/api": { target: process.env.KOKPIT_API ?? "http://127.0.0.1:8501", changeOrigin: true } },
  },
  test: { environment: "node" },
}));
