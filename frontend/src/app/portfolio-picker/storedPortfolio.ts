/** Clave de la última cartera elegida en este navegador (T4-13). */
export const PORTFOLIO_STORAGE_KEY = "kairos-portfolio";

/** Última cartera elegida, o null si no hay o el almacenamiento está bloqueado. */
export function readStoredPortfolio(): string | null {
  try {
    return localStorage.getItem(PORTFOLIO_STORAGE_KEY) || null;
  } catch {
    return null; // modo privado o políticas del navegador
  }
}

export function writeStoredPortfolio(id: string): void {
  try {
    localStorage.setItem(PORTFOLIO_STORAGE_KEY, id);
  } catch {
    // sin persistencia: la elección vale mientras dure la URL
  }
}
