/// <reference types="vitest/config" />
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// El frontend llama a /api/v1/...; Vite reenvía la ruta tal cual al backend (SPEC §11).
// Fuera de Docker: http://localhost:8000. Dentro de Docker (compose): KAIROS_API_PROXY=http://backend:8000.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const target = env.KAIROS_API_PROXY || process.env.KAIROS_API_PROXY || "http://localhost:8000";
  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: true,
      port: 5173,
      proxy: {
        // ws: también el WebSocket de voz (`/api/v1/voice/stt`).
        "/api": { target, changeOrigin: true, ws: true },
      },
    },
    test: {
      environment: "jsdom",
      include: ["src/**/*.test.{ts,tsx}"],
    },
  };
});
