import { useEffect, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { apiGet } from "../../api/client";
import type { AssetOut } from "../../api/generated/schema";

/** Por debajo de esto no se busca: con una letra salen casi todos los activos. */
export const MIN_QUERY_LENGTH = 2;
const DEBOUNCE_MS = 250;

function useDebounced<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}

/** Autocompletar por ISIN, ticker o nombre (`GET /assets/lookup?q=`, RF-01). */
export function useAssetLookup(query: string) {
  const q = useDebounced(query.trim(), DEBOUNCE_MS);
  const enabled = q.length >= MIN_QUERY_LENGTH;
  const result = useQuery({
    queryKey: ["assets", "lookup", q],
    queryFn: async ({ signal }) => {
      const data = await apiGet<AssetOut[] | AssetOut>(
        `/assets/lookup?q=${encodeURIComponent(q)}`,
        { mock: "AssetOut", signal },
      );
      return Array.isArray(data) ? data : [data];
    },
    enabled,
    placeholderData: keepPreviousData,
    staleTime: 5 * 60_000,
  });
  return { ...result, enabled, settled: q === query.trim() };
}
