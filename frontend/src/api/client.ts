/**
 * Cliente de API. Todas las llamadas al backend pasan por aquí (regla de CLAUDE.md).
 *
 * - Normal: fetch a `/api/v1/...` (Vite lo reenvía al backend, ver vite.config.ts).
 * - Con VITE_USE_MOCKS=true: lee `src/api/mocks/<Modelo>.json` si existe. Esa carpeta la
 *   rellena `make gen-api` (T0-03) copiando backend/app/schemas/examples/*.json.
 *   Mientras no exista, no se inventa ningún dato: la llamada falla con `mock_missing`
 *   y la pantalla muestra su estado vacío.
 */
const BASE = "/api/v1";
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === "true";

// Sin ficheros en mocks/ el glob devuelve {}: es válido.
const mockModules = import.meta.glob("./mocks/*.json", { eager: true, import: "default" });

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | undefined;
  /** `details` de `ErrorOut` (p. ej. `asset_id` en un 404), o {} si no vino. */
  readonly details: Record<string, unknown>;
  constructor(message: string, status: number, code?: string, details?: Record<string, unknown>) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details ?? {};
  }
}

/** Convierte una respuesta no-OK en `ApiError` leyendo el `ErrorOut` si lo hay. */
export async function toApiError(method: string, path: string, res: Response): Promise<ApiError> {
  let code: string | undefined;
  let details: Record<string, unknown> | undefined;
  try {
    const body = (await res.json()) as { code?: string; details?: Record<string, unknown> };
    code = body.code;
    details = body.details;
  } catch {
    // cuerpo no JSON
  }
  return new ApiError(`${method} ${path} -> ${res.status}`, res.status, code, details);
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
  if (!res.ok) throw await toApiError("GET", path, res);
  return (await res.json()) as T;
}

/**
 * POST con cuerpo JSON. Con mocks no se escribe nada: devuelve el ejemplo del modelo de
 * respuesta (o `mock_missing`), para poder recorrer la pantalla sin backend.
 */
export async function apiPost<T>(path: string, body?: unknown, opts: GetOptions = {}): Promise<T> {
  if (USE_MOCKS && opts.mock) {
    const m = getMock<T>(opts.mock);
    if (m !== undefined) return m;
    throw new ApiError(`No hay mock para ${opts.mock}`, 404, "mock_missing");
  }
  const init: RequestInit = {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
  };
  if (body !== undefined) init.body = JSON.stringify(body);
  if (opts.signal) init.signal = opts.signal;
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) throw await toApiError("POST", path, res);
  return (await res.json()) as T;
}

/** PATCH con cuerpo JSON (solo los campos que cambian). Con mocks, igual que `apiPost`. */
export async function apiPatch<T>(path: string, body: unknown, opts: GetOptions = {}): Promise<T> {
  if (USE_MOCKS && opts.mock) {
    const m = getMock<T>(opts.mock);
    if (m !== undefined) return m;
    throw new ApiError(`No hay mock para ${opts.mock}`, 404, "mock_missing");
  }
  const init: RequestInit = {
    method: "PATCH",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
  if (opts.signal) init.signal = opts.signal;
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) throw await toApiError("PATCH", path, res);
  return (await res.json()) as T;
}
