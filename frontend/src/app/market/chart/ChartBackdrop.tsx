/**
 * Halo dorado estático en la esquina de la tarjeta (decorativo). Sin líneas ni movimiento.
 * Va recortado en su propia capa: la tarjeta no recorta su contenido, para que la tarjeta de una
 * noticia (T2-22) pueda salir por debajo de la gráfica sin cortarse.
 */
export function ChartBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden rounded-card" aria-hidden="true">
      <div className="kchart-glow" />
    </div>
  );
}
