import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import type { NewsItemOut } from "../../api/generated/schema";
import nvda from "../../api/mocks/NewsItemOut.json";
import { NewsSection } from "./NewsSection";
import { useTopNews } from "./useTopNews";

vi.mock("./useTopNews", () => ({ useTopNews: vi.fn() }));

type Query = ReturnType<typeof useTopNews>;

function renderWith(state: Partial<Query>) {
  vi.mocked(useTopNews).mockReturnValue({
    data: undefined,
    isPending: false,
    isError: false,
    ...state,
  } as Query);
  return render(
    <MemoryRouter>
      <NewsSection portfolioId="laura" newsHref="/noticias?p=laura" />
    </MemoryRouter>,
  );
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("NewsSection", () => {
  it("mientras carga, un esqueleto anunciado", () => {
    renderWith({ isPending: true });
    expect(screen.getByRole("status", { name: "Cargando noticias" })).toBeTruthy();
  });

  it("sin noticias en 24 horas lo dice y enlaza a Noticias", () => {
    renderWith({ data: [] });
    expect(screen.getByText(/últimas 24 horas no ha salido ninguna noticia/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Ver todas las noticias" }).getAttribute("href")).toBe(
      "/noticias?p=laura",
    );
  });

  it("si falla, un aviso sin cifras", () => {
    renderWith({ isError: true });
    expect(screen.getByText(/no podemos cargar las noticias/)).toBeTruthy();
  });

  it("con noticias, el carrusel", () => {
    renderWith({ data: [nvda as NewsItemOut] });
    expect(screen.getByRole("heading", { level: 2, name: "Lo que más mueve tu cartera hoy" })).toBeTruthy();
    expect(screen.getByRole("heading", { level: 3, name: nvda.title })).toBeTruthy();
  });
});
