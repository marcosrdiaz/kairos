import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import newsExample from "../../../../api/mocks/NewsItemOut.json";
import pendingExample from "../../../../api/mocks/NewsItemOut.pending.json";
import type { NewsItemOut } from "../../../../api/generated/schema";
import { TraceProvider } from "../../../../components/trace/TraceProvider";
import { AlertNewsCard } from "./AlertNewsCard";
import { AlertNewsDot } from "./AlertNewsDot";
import { createNewsMarkerStore } from "./newsMarkerStore";
import type { AlertNewsMarker } from "./useAlertNewsMarkers";

afterEach(cleanup);

function marker(news: NewsItemOut): AlertNewsMarker {
  return {
    news,
    marketDate: news.published_at,
    date: "2026-11-06T00:00:00Z",
    value: 42_363.67,
  };
}

function renderCard(news: NewsItemOut, width = 320) {
  const store = createNewsMarkerStore();
  render(
    <TraceProvider>
      <AlertNewsCard store={store} id="news-card" width={width} />
    </TraceProvider>,
  );
  act(() => store.set({ marker: marker(news), x: width - 10, y: 80 }));
  return { store, card: screen.getByRole("tooltip") };
}

describe("tarjeta de noticia en la gráfica", () => {
  it("muestra el impacto estimado con rango, plazo, trazabilidad y fallback de mercado", () => {
    const news = newsExample as NewsItemOut;
    const { card } = renderCard(news, 250);

    expect(card.textContent).toContain(news.title);
    expect(card.textContent).toContain(news.summary);
    expect(card.textContent).toContain("Impacto estimado en tu cartera");
    expect(card.textContent).toMatch(/-270.*-110/);
    expect(card.textContent).toContain("A 5 sesiones");
    expect(card.textContent).toContain("movimiento medido del mercado no está disponible");
    expect(screen.getByRole("button", { name: "¿De dónde sale?" })).toBeTruthy();
    expect(card.querySelector("[data-calc-id]")?.getAttribute("data-calc-id")).toBe(
      news.estimate?.calc_id,
    );
    expect(card.style.width).toBe("250px");
    expect(card.style.left).toBe("0px");
  });

  it("etiqueta como medido el rango real devuelto por la API", () => {
    const original = newsExample as NewsItemOut;
    const news: NewsItemOut = {
      ...original,
      estimate: original.estimate ? { ...original.estimate, status: "measured" } : null,
    };
    const { card } = renderCard(news);

    expect(card.textContent).toContain("Impacto medido en tu cartera");
    expect(card.textContent).toContain("movimiento medido del mercado no está disponible");
  });

  it("no presenta cifras si la estimación sigue pendiente", () => {
    const news = pendingExample as NewsItemOut;
    const { card } = renderCard(news);

    expect(card.textContent).toContain("Impacto en tu cartera pendiente de medición");
    expect(card.textContent).toContain("no hay un rango disponible");
    expect(card.textContent).not.toContain("€");
    expect(card.querySelector("[data-calc-id]")).toBeNull();
    expect(screen.queryByRole("button", { name: "¿De dónde sale?" })).toBeNull();
  });

  it("anuncia fecha e impacto, y abre la tarjeta con foco de teclado", () => {
    const news = newsExample as NewsItemOut;
    const active = marker(news);
    const store = createNewsMarkerStore();
    const onChartKey = vi.fn();
    render(
      <svg onKeyDown={onChartKey}>
        <AlertNewsDot cx={120} cy={80} marker={active} store={store} cardId="news-card" />
      </svg>,
    );
    const dot = screen.getByRole("button");
    expect(dot.getAttribute("aria-label")).toMatch(/Noticia con aviso del 26 de febrero de 2025/);
    expect(dot.getAttribute("aria-label")).toContain("Impacto estimado en tu cartera");
    fireEvent.focus(dot);
    expect(store.get()?.marker.news.id).toBe(news.id);
    fireEvent.keyDown(dot, { key: "ArrowLeft" });
    expect(onChartKey).not.toHaveBeenCalled();
    fireEvent.keyDown(dot, { key: "Escape" });
    expect(store.get()).toBeNull();
  });
});
