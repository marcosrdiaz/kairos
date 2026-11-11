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
    expect(card.style.maxHeight).toBe("13rem");
    expect(card.className).toContain("overflow-y-auto");
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

  it("muestra la categoría y la fecha de la noticia, con título y resumen recortados", () => {
    const news = newsExample as NewsItemOut;
    const { card } = renderCard(news, 400);

    expect(card.textContent).not.toContain("Ejemplo visual");
    expect(card.textContent).toContain("Resultados");
    expect(card.querySelector("p.line-clamp-2.font-semibold")?.textContent).toBe(news.title);
    expect(card.querySelector("p.line-clamp-1.text-ink-muted")?.textContent).toBe(news.summary);
  });

  it("en una gráfica estrecha oculta el resumen y el aviso largo para no tapar el resto", () => {
    const { card } = renderCard(newsExample as NewsItemOut, 320);
    const summary = card.querySelector("p.line-clamp-1.text-ink-muted");
    expect(summary?.className).toContain("hidden");
    expect(card.querySelector("p.text-xs.hidden")?.textContent).toContain("no está disponible");
    expect(screen.getByRole("button", { name: "¿De dónde sale?" })).toBeTruthy(); // la traza se queda
  });

  it("con la altura de la gráfica, limita la altura de la tarjeta a esa altura", () => {
    const store = createNewsMarkerStore();
    render(
      <TraceProvider>
        <AlertNewsCard store={store} id="news-card" width={600} height={300} />
      </TraceProvider>,
    );
    act(() => store.set({ marker: marker(newsExample as NewsItemOut), x: 300, y: 250 }));
    expect(screen.getByRole("tooltip").style.maxHeight).toBe("min(21rem, 292px)");
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

  it("usa los colores emparejados de la paleta para que el pin contraste en ambos temas", () => {
    const news = newsExample as NewsItemOut;
    const store = createNewsMarkerStore();
    render(
      <svg>
        <AlertNewsDot cx={120} cy={80} marker={marker(news)} store={store} cardId="news-card" />
      </svg>,
    );
    const dot = screen.getByRole("button");
    const circles = dot.querySelectorAll("circle");
    expect(circles[0]?.getAttribute("r")).toBe("21");
    expect(circles[1]?.getAttribute("r")).toBe("16");
    expect(circles[1]?.getAttribute("fill")).toBe("var(--kairos-color-primary)");
    expect(dot.querySelector("path")?.getAttribute("stroke")).toBe("var(--kairos-color-on-primary)");
    expect(dot.querySelector("path")?.getAttribute("d")).toBe(
      "M1.5 10.5h9M3 10V6.5M6 10V3.5M9 10V5",
    );
  });

  describe("plazo en singular y plural", () => {
    const withHorizon = (sessions: number) => {
      const news = newsExample as NewsItemOut;
      return { ...news, estimate: { ...news.estimate!, horizon_sessions: sessions } } as NewsItemOut;
    };

    it.each([
      [1, "A 1 sesión"],
      [5, "A 5 sesiones"],
    ])("tarjeta con plazo %i: «%s»", (sessions, text) => {
      const { card } = renderCard(withHorizon(sessions));
      expect(card.textContent).toContain(text);
      expect(card.textContent).not.toContain("1 sesiones");
    });

    it.each([
      [1, "a 1 sesión."],
      [5, "a 5 sesiones."],
    ])("etiqueta del punto con plazo %i: «%s»", (sessions, text) => {
      render(
        <svg>
          <AlertNewsDot cx={120} cy={80} marker={marker(withHorizon(sessions))} store={createNewsMarkerStore()} cardId="news-card" />
        </svg>,
      );
      expect(screen.getByRole("button").getAttribute("aria-label")).toContain(text);
    });
  });
});
