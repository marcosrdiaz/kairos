import { defineConfig, devices } from "@playwright/test";

/**
 * E2E del guion de demo (T3-02): la app real contra el backend real en modo offline.
 *
 * `npm run e2e` (en `frontend/`). Si el stack no está levantado, `e2e/global-setup.ts` lo levanta
 * con Docker Compose y el override `e2e/compose.e2e.yml` (sin claves: plantillas y voz mock).
 * Los tests resetean la demo, así que borran lo que hubiera: no los lances durante un ensayo.
 *
 * - `E2E_BASE_URL`: dónde está la app (por defecto, el nginx de Compose en el puerto 5173).
 * - `E2E_BROWSER_CHANNEL`: `msedge` o `chrome` para usar un navegador instalado en vez del
 *   Chromium de Playwright (`npx playwright install chromium`).
 */
const baseURL = process.env.E2E_BASE_URL || "http://localhost:5173";
const channel = process.env.E2E_BROWSER_CHANNEL || undefined;

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.e2e.ts",
  outputDir: "./e2e/test-results",
  // La demo es un estado global del backend (reset, replay): un test cada vez y en orden.
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 60_000,
  // El widget y los avisos se refrescan por polling cada 5 s (T2-13).
  expect: { timeout: 15_000 },
  reporter: [["list"], ["html", { outputFolder: "./e2e/report", open: "never" }]],
  globalSetup: "./e2e/global-setup.ts",
  use: {
    baseURL,
    locale: "es-ES",
    timezoneId: "Europe/Madrid",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "escritorio",
      // Escritorio: el asistente es un panel lateral y el selector de cartera está en la barra.
      use: { ...devices["Desktop Chrome"], channel, viewport: { width: 1440, height: 900 } },
    },
  ],
});
