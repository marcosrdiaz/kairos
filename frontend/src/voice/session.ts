/**
 * `session_id` de `/ask`: lo genera el frontend al abrir la app y el backend lo usa para saber
 * si toca el aviso de IA (solo la primera vez de la sesión). Dura lo que la pestaña.
 */
const KEY = "kairos.session_id";

function newId(): string {
  const random =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().replace(/-/g, "")
      : Math.random().toString(36).slice(2) + Date.now().toString(36);
  return `ses_${random.slice(0, 16)}`;
}

let cached: string | null = null;

export function getSessionId(): string {
  if (cached) return cached;
  try {
    cached = sessionStorage.getItem(KEY);
    if (!cached) {
      cached = newId();
      sessionStorage.setItem(KEY, cached);
    }
  } catch {
    cached = newId(); // sin sessionStorage (modo privado estricto): vale para esta carga
  }
  return cached;
}
