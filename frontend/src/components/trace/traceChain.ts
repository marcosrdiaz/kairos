import type { TraceOut } from "../../api/generated/schema";

/** Un cálculo del que parte la cifra. `trace: null` = esa traza no está disponible. */
export interface TraceOrigin {
  calcId: string;
  trace: TraceOut | null;
}

export interface TraceChain {
  root: TraceOut;
  origins: TraceOrigin[];
  /** Quedaban cálculos de origen por encima de `MAX_ORIGINS`. */
  truncated: boolean;
}

/** Tope de peticiones por cifra: una cadena no debe disparar decenas de llamadas sin límite. */
export const MAX_ORIGINS = 40;

/**
 * Recorre `parent_calc_ids` por niveles hasta que no quedan padres. El endpoint no los expande.
 * Si falla la traza pedida, falla todo (la pantalla lo explica). Si falla un padre, ese padre
 * queda como «no disponible» y el resto se muestra. El conjunto `seen` evita repetir cálculos
 * compartidos y protege de ciclos.
 */
export async function loadTraceChain(
  calcId: string,
  fetchTrace: (id: string) => Promise<TraceOut>,
): Promise<TraceChain> {
  const root = await fetchTrace(calcId);
  const seen = new Set([calcId, root.calc_id]);
  const origins: TraceOrigin[] = [];
  let truncated = false;
  let level = root.parent_calc_ids ?? [];
  while (level.length > 0) {
    const fresh = [...new Set(level)].filter((id) => !seen.has(id));
    const batch = fresh.slice(0, MAX_ORIGINS - origins.length);
    truncated ||= batch.length < fresh.length;
    batch.forEach((id) => seen.add(id));
    const loaded = await Promise.all(
      batch.map(async (id) => ({ calcId: id, trace: await fetchTrace(id).catch(() => null) })),
    );
    origins.push(...loaded);
    level = loaded.flatMap((origin) => origin.trace?.parent_calc_ids ?? []);
  }
  return { root, origins, truncated };
}
