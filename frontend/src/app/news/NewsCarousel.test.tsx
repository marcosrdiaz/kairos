import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import type { EventImpactOut } from "../../api/generated/schema";
import bce from "../../api/mocks/EventImpactOut.json";
import nvda from "../../api/mocks/EventImpactOut.nvda.json";
import { AUTO_ADVANCE_MS } from "./labels";
import { NewsCarousel } from "./NewsCarousel";

const EVENTS = [bce as EventImpactOut, nvda as EventImpactOut];

function renderCarousel(events = EVENTS) {
  return render(
    <MemoryRouter>
      <NewsCarousel events={events} panelHref="/panel" />
    </MemoryRouter>,
  );
}

const slide = () => screen.getByRole("group");

beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("NewsCarousel", () => {
  it("muestra una noticia con su posición, rango y confianza", () => {
    renderCarousel();
    expect(slide().getAttribute("aria-roledescription")).toBe("noticia");
    expect(slide().getAttribute("aria-label")).toBe("1 de 2");
    expect(screen.getByRole("heading", { level: 3, name: EVENTS[0]!.title })).toBeTruthy();
    expect(screen.getByText(/entre -10\s€ y 190\s€/)).toBeTruthy();
    expect(screen.getByText("Confianza media")).toBeTruthy();
    expect(slide().getAttribute("data-calc-id")).toBe(EVENTS[0]!.calc_id);
  });

  it("sin explicación todavía, enseña la cadena causal", () => {
    renderCarousel([nvda as EventImpactOut]);
    expect(screen.getByText(nvda.causal_chain.join(" → "))).toBeTruthy();
  });

  it("las flechas avanzan y retroceden en círculo", () => {
    renderCarousel();
    fireEvent.click(screen.getByRole("button", { name: "Noticia siguiente" }));
    expect(slide().getAttribute("aria-label")).toBe("2 de 2");
    fireEvent.click(screen.getByRole("button", { name: "Noticia siguiente" }));
    expect(slide().getAttribute("aria-label")).toBe("1 de 2");
    fireEvent.click(screen.getByRole("button", { name: "Noticia anterior" }));
    expect(slide().getAttribute("aria-label")).toBe("2 de 2");
  });

  it("avanza solo cada 10 s y no se anuncia mientras rota", () => {
    renderCarousel();
    expect(document.getElementById("news-slides")?.getAttribute("aria-live")).toBe("off");
    act(() => vi.advanceTimersByTime(AUTO_ADVANCE_MS - 1));
    expect(slide().getAttribute("aria-label")).toBe("1 de 2");
    act(() => vi.advanceTimersByTime(1));
    expect(slide().getAttribute("aria-label")).toBe("2 de 2");
  });

  it("el botón de pausa detiene el avance y activa el anuncio", () => {
    renderCarousel();
    fireEvent.click(screen.getByRole("button", { name: "Pausar el pase automático" }));
    expect(screen.getByRole("button", { name: "Reanudar el pase automático" })).toBeTruthy();
    expect(document.getElementById("news-slides")?.getAttribute("aria-live")).toBe("polite");
    act(() => vi.advanceTimersByTime(AUTO_ADVANCE_MS * 3));
    expect(slide().getAttribute("aria-label")).toBe("1 de 2");
  });

  it("se detiene con el ratón encima", () => {
    const { container } = renderCarousel();
    fireEvent.mouseEnter(container.firstElementChild!);
    act(() => vi.advanceTimersByTime(AUTO_ADVANCE_MS * 2));
    expect(slide().getAttribute("aria-label")).toBe("1 de 2");
    fireEvent.mouseLeave(container.firstElementChild!);
    act(() => vi.advanceTimersByTime(AUTO_ADVANCE_MS));
    expect(slide().getAttribute("aria-label")).toBe("2 de 2");
  });

  it("los puntos llevan a cada noticia y marcan la actual", () => {
    renderCarousel();
    const second = screen.getByRole("button", { name: `Noticia 2: ${EVENTS[1]!.title}` });
    fireEvent.click(second);
    expect(second.getAttribute("aria-current")).toBe("true");
    expect(slide().getAttribute("aria-label")).toBe("2 de 2");
  });

  it("con una sola noticia no hay controles", () => {
    renderCarousel([bce as EventImpactOut]);
    expect(screen.queryByRole("button", { name: "Noticia siguiente" })).toBeNull();
    expect(screen.queryByRole("button", { name: /pase automático/ })).toBeNull();
  });
});
