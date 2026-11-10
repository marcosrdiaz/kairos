/** Ruta del detalle de una posición (T2-23), conservando la cartera elegida (`?p=`). */
export function assetHref(assetId: string, portfolioId: string): string {
  return `/activo/${encodeURIComponent(assetId)}?p=${encodeURIComponent(portfolioId)}`;
}
