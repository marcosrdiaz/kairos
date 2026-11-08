/// <reference types="vitest/config" />
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// El frontend llama siempre a /api/...; Vite lo reenvía al backend quitando el prefijo.
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
        "/api": { target, changeOrigin: true, rewrite: (path: string) => path.replace(/^\/api/, "") },
      },
    },
    test: {
      environment: "jsdom",
      include: ["src/**/*.test.{ts,tsx}"],
    },
  };
});
