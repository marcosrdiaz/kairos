/**
 * Cliente de API. Todas las llamadas al backend pasan por aquí (regla de CLAUDE.md).
 *
 * - Normal: fetch a `/api/...` (Vite lo reenvía al backend, ver vite.config.ts).
 * - Con VITE_USE_MOCKS=true: lee `src/api/mocks/<Modelo>.json` si existe. Esa carpeta la
 *   rellena `make gen-api` (T0-03) copiando backend/app/schemas/examples/*.json.
 *   Mientras no exista, no se inventa ningún dato: la llamada falla con `mock_missing`
 *   y la pantalla muestra su estado vacío.
 */
const BASE = "/api";
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === "true";

// Sin ficheros en mocks/ el glob devuelve {}: es válido.
const mockModules = import.meta.glob("./mocks/*.json", { eager: true, import: "default" });

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | undefined;
  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

/** Devuelve el mock de un modelo por su nombre (p. ej. "PortfolioOut"), o undefined. */
export function getMock<T>(model: string): T | undefined {
  return mockModules[`./mocks/${model}.json`] as T | undefined;
}

export interface GetOptions {
  /** Nombre del esquema cuyo ejemplo sirve de mock para esta ruta. */
  mock?: string;
  signal?: AbortSignal;
}

export async function apiGet<T>(path: string, opts: GetOptions = {}): Promise<T> {
  if (USE_MOCKS && opts.mock) {
    const m = getMock<T>(opts.mock);
    if (m !== undefined) return m;
    throw new ApiError(`No hay mock para ${opts.mock}`, 404, "mock_missing");
  }
  const init: RequestInit = { headers: { Accept: "application/json" } };
  if (opts.signal) init.signal = opts.signal;
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    let code: string | undefined;
    try {
      code = ((await res.json()) as { code?: string }).code;
    } catch {
      // cuerpo no JSON
    }
    throw new ApiError(`GET ${path} -> ${res.status}`, res.status, code);
  }
  return (await res.json()) as T;
}
