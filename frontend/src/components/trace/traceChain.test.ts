import { describe, expect, it, vi } from "vitest";
import type { TraceOut } from "../../api/generated/schema";
import { ApiError } from "../../api/client";
import { MAX_ORIGINS, loadTraceChain } from "./traceChain";

function trace(calcId: string, parents: string[] = []): TraceOut {
  return {
    calc_id: calcId,
    kind: "valuation",
    created_at: "2026-11-08T18:00:00Z",
    formula: "a = b",
    inputs: {},
    outputs: {},
    sources: [],
    parent_calc_ids: parents,
  };
}

function fetcher(traces: TraceOut[]) {
  const byId = new Map(traces.map((t) => [t.calc_id, t]));
  return vi.fn(async (id: string) => {
    const found = byId.get(id);
    if (!found) throw new ApiError("not found", 404, "NOT_FOUND");
    return found;
  });
}

describe("loadTraceChain", () => {
  it("sin padres devuelve solo la traza pedida", async () => {
    const chain = await loadTraceChain("a", fetcher([trace("a")]));
    expect(chain.root.calc_id).toBe("a");
    expect(chain.origins).toEqual([]);
    expect(chain.truncated).toBe(false);
  });

  it("recorre todos los niveles hasta que no quedan padres", async () => {
    const chain = await loadTraceChain("a", fetcher([trace("a", ["b"]), trace("b", ["c"]), trace("c")]));
    expect(chain.origins.map((o) => o.calcId)).toEqual(["b", "c"]);
  });

  it("no repite un padre compartido", async () => {
    const fetchTrace = fetcher([trace("a", ["b", "c"]), trace("b", ["d"]), trace("c", ["d"]), trace("d")]);
    const chain = await loadTraceChain("a", fetchTrace);
    expect(chain.origins.map((o) => o.calcId)).toEqual(["b", "c", "d"]);
    expect(fetchTrace.mock.calls.filter(([id]) => id === "d")).toHaveLength(1);
  });

  it("termina aunque haya un ciclo", async () => {
    const chain = await loadTraceChain("a", fetcher([trace("a", ["b"]), trace("b", ["a"])]));
    expect(chain.origins.map((o) => o.calcId)).toEqual(["b"]);
  });

  it("un padre que no existe queda como no disponible y no rompe la traza", async () => {
    const chain = await loadTraceChain("a", fetcher([trace("a", ["falta", "b"]), trace("b")]));
    expect(chain.origins).toEqual([
      { calcId: "falta", trace: null },
      { calcId: "b", trace: trace("b") },
    ]);
  });

  it("si falla la traza pedida, propaga el error", async () => {
    await expect(loadTraceChain("falta", fetcher([]))).rejects.toMatchObject({ status: 404 });
  });

  it("corta en el tope de cálculos y lo indica", async () => {
    const parents = Array.from({ length: MAX_ORIGINS + 5 }, (_, i) => `p${i}`);
    const fetchTrace = fetcher([trace("a", parents), ...parents.map((id) => trace(id))]);
    const chain = await loadTraceChain("a", fetchTrace);
    expect(chain.origins).toHaveLength(MAX_ORIGINS);
    expect(chain.truncated).toBe(true);
  });
});
