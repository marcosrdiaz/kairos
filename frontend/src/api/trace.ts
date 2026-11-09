import { apiGet } from "./client";
import type { TraceOut } from "./generated/schema";

/** `GET /traces/{calc_id}`: cálculo, entradas, salidas y fuentes de una cifra (RF-19). */
export function getTrace(calcId: string, signal?: AbortSignal): Promise<TraceOut> {
  return apiGet<TraceOut>(`/traces/${encodeURIComponent(calcId)}`, {
    mock: "TraceOut",
    ...(signal ? { signal } : {}),
  });
}
