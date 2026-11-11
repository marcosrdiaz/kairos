import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import type { NewsItemOut } from "../../api/generated/schema";
import nvda from "../../api/mocks/NewsItemOut.json";
import { AUTO_ADVANCE_MS } from "./labels";
import { NewsCarousel } from "./NewsCarousel";

const FIRST = nvda as NewsItemOut;
const SECOND: NewsItemOut = {
  ...FIRST,
  id: "news_second",
  title: "Otra noticia que mueve la cartera",
  category: "central_bank",
  causal_chain: [],
  summary: "Resumen de la fuente.",
};
const EVENTS = [FIRST, SECOND];

function renderCarousel(items = EVENTS) {
  return render(
    <MemoryRouter>
      <NewsCarousel items={items} newsHref="/noticias" />
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
  it("muestra una noticia con su posición, rango trazado, estado y confianza", () => {
    renderCarousel();
    expect(slide().getAttribute("aria-roledescription")).toBe("noticia");
    expect(slide().getAttribute("aria-label")).toBe("1 de 2");
    expect(screen.getByRole("heading", { level: 3, name: FIRST.title })).toBeTruthy();
    expect(screen.getByText(/entre -270\s€ y -110\s€/)).toBeTruthy();
    expect(screen.getByText("Estimado")).toBeTruthy();
    expect(screen.getByText("Confianza media")).toBeTruthy();
    expect(slide().getAttribute("data-calc-id")).toBe(FIRST.estimate!.calc_id);
    expect(screen.getByText(`Fuente: ${FIRST.source.label}`)).toBeTruthy();
    expect(screen.getByRole("link", { name: /Ver todas las noticias/ }).getAttribute("href")).toBe(
      "/noticias",
    );
  });

  it("enseña la cadena causal y, si no la hay, el resumen de la fuente", () => {
    renderCarousel();
    expect(screen.getByText(FIRST.causal_chain.join(" → "))).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Noticia siguiente" }));
    expect(screen.getByText("Resumen de la fuente.")).toBeTruthy();
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

  it("sin puntos: el contador y las flechas son la navegación", () => {
    renderCarousel();
    expect(screen.queryByRole("button", { name: /^Noticia 2:/ })).toBeNull();
    expect(screen.getByText("1 / 2")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Noticia siguiente" }));
    expect(screen.getByText("2 / 2")).toBeTruthy();
    expect(slide().getAttribute("aria-label")).toBe("2 de 2");
  });

  it("con una sola noticia no hay controles", () => {
    renderCarousel([FIRST]);
    expect(screen.queryByRole("button", { name: "Noticia siguiente" })).toBeNull();
    expect(screen.queryByRole("button", { name: /pase automático/ })).toBeNull();
  });
});
