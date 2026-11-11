import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import alertExample from "../../../../api/mocks/AlertOut.news_estimate.json";
import newsExample from "../../../../api/mocks/NewsItemOut.json";
import history from "../../../../api/mocks/PortfolioHistoryOut.json";
import type { AlertOut, NewsItemOut, PortfolioHistoryOut } from "../../../../api/generated/schema";
import { toRows } from "../chartFormat";
import { HistoryTable } from "../HistoryTable";
import { useAlertNewsMarkers } from "./useAlertNewsMarkers";
import { useEventMarkers } from "./useEventMarkers";

const rows = toRows(history as PortfolioHistoryOut);
const json = (body: unknown) => new Response(JSON.stringify(body), { headers: { "Content-Type": "application/json" } });

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe("marcadores de Inicio respaldados por avisos", () => {
  it("sin avisos no muestra puntos aunque existan eventos", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => json(String(input).endsWith("/alerts") ? [] : [])));
    const { result } = renderHook(() => useEventMarkers("laura", rows), { wrapper });
    await waitFor(() => expect(result.current).toEqual([]));
  });

  it("pide por id solo la noticia avisada y la sitúa en su cierre", async () => {
    const news = { ...newsExample, published_at: "2026-11-06T10:00:00Z" } as NewsItemOut;
    const alert = { ...alertExample, news_id: news.id } as AlertOut;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      return json(url.endsWith("/alerts") ? [alert] : url.includes("/news/") ? news : []);
    });
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useAlertNewsMarkers("laura", rows), { wrapper });
    await waitFor(() => expect(result.current).toHaveLength(1));
    expect(result.current[0]?.news.id).toBe(news.id);
    expect(result.current[0]?.date).toBe("2026-11-06T00:00:00Z");
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith(`/news/${news.id}`))).toBe(true);
  });

  it("incluye la noticia avisada y su cifra trazable en la tabla alternativa", () => {
    const news = { ...newsExample, published_at: "2026-11-06T10:00:00Z" } as NewsItemOut;
    const firstRow = rows[0]!;
    render(
      <HistoryTable
        history={history as PortfolioHistoryOut}
        periodName="Último mes"
        newsMarkers={[{ news, marketDate: news.published_at, date: firstRow.date, value: firstRow.value }]}
      />,
    );
    fireEvent.click(screen.getByText(/^Ver tabla/));
    const details = document.querySelector("details") as HTMLDetailsElement;
    details.open = true;
    fireEvent(details, new Event("toggle"));
    expect(screen.getByText(news.title)).toBeTruthy();
    expect(screen.getByText(/impacto estimado entre .* a 5 sesiones/)).toBeTruthy();
    expect(document.querySelector(`[data-calc-id="${news.estimate?.calc_id}"]`)).toBeTruthy();
  });
});
