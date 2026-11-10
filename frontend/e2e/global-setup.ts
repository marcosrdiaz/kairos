import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { request, type FullConfig } from "@playwright/test";

/**
 * Antes de los E2E: que el stack esté arriba y en modo offline.
 *
 * - Si `/health` no responde, levanta el stack de `make up` con el override offline
 *   (`compose.e2e.yml`). Con `E2E_NO_STACK=1` no lo levanta y falla con instrucciones.
 * - Comprueba el modo offline: reloj de demo fijado y frase de estado de plantilla. Si responde
 *   Claude real (un stack levantado con el `.env` de alguien), las respuestas cambian en cada
 *   pasada y el E2E deja de ser repetible: se para con el comando para levantarlo bien.
 */
const ROOT = fileURLToPath(new URL("../..", import.meta.url));
const COMPOSE = ["compose", "-f", "docker-compose.yml", "-f", "frontend/e2e/compose.e2e.yml"];
const UP = `docker ${COMPOSE.join(" ")} up --build -d --wait`;
const DEMO_CLOCK = "2026-11-06T18:00:00";

async function health(baseURL: string): Promise<{ demo_mode: boolean; now: string } | null> {
  const api = await request.newContext({ baseURL });
  try {
    const response = await api.get("/api/v1/health", { timeout: 5_000 });
    return response.ok() ? await response.json() : null;
  } catch {
    return null;
  } finally {
    await api.dispose();
  }
}

function startStack(): void {
  console.log(`E2E: el stack no responde; lo levanto en modo offline (${UP})`);
  // El backend primero: `seed` y `backend` comparten imagen y, construidas a la vez, la caché
  // de Docker a veces falla («parent snapshot does not exist»).
  execFileSync("docker", [...COMPOSE, "build", "backend"], { cwd: ROOT, stdio: "inherit" });
  execFileSync("docker", [...COMPOSE, "up", "--build", "-d", "--wait"], {
    cwd: ROOT,
    stdio: "inherit",
  });
}

async function assertOffline(baseURL: string): Promise<void> {
  const status = await health(baseURL);
  if (!status) throw new Error(`E2E: ${baseURL}/api/v1/health no responde tras levantar el stack`);
  const wrong = `Para los E2E hace falta el stack en modo offline. Desde la raíz: ${UP}`;
  if (!status.demo_mode || !status.now.startsWith(DEMO_CLOCK)) {
    throw new Error(`E2E: el backend no tiene el reloj de demo (${status.now}). ${wrong}`);
  }
  const api = await request.newContext({ baseURL });
  try {
    const reset = await api.post("/api/v1/demo/reset", { data: { preload: true } });
    if (!reset.ok()) throw new Error(`E2E: /demo/reset respondió ${reset.status()}`);
    const laura = await (await api.get("/api/v1/portfolios/laura/status")).json();
    if (laura.sentence_status !== "template") {
      throw new Error(`E2E: el backend responde con Claude real (hay clave). ${wrong}`);
    }
  } finally {
    await api.dispose();
  }
}

export default async function globalSetup(config: FullConfig): Promise<void> {
  const baseURL = config.projects[0]?.use.baseURL ?? "http://localhost:5173";
  if (!(await health(baseURL))) {
    if (process.env.E2E_NO_STACK) {
      throw new Error(`E2E: ${baseURL} no responde. Levanta el stack: ${UP}`);
    }
    startStack();
  }
  await assertOffline(baseURL);
}
