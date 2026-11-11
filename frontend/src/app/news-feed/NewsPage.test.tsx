import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { NewsItemOut } from "../../api/generated/schema";
import estimated from "../../api/mocks/NewsItemOut.json";
import notRelevant from "../../api/mocks/NewsItemOut.not_relevant.json";
import pending from "../../api/mocks/NewsItemOut.pending.json";
import { filterNews } from "../../api/hooks/useNews";
import { NewsPage } from "./NewsPage";

const ALL = [estimated, pending, notRelevant] as NewsItemOut[];
let fetchMock: ReturnType<typeof vi.fn>;

/** Responde como la ruta: aplica `category` y `affecting` de la URL. */
function serveNews(items: NewsItemOut[]) {
  fetchMock.mockImplementation((url: string) => {
    const params = new URL(url, "http://localhost").searchParams;
    const body = filterNews(items, {
      category: (params.get("category") as NewsItemOut["category"] | null) ?? null,
      affecting: params.get("affecting") !== "false",
    });
    return Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/noticias?p=laura"]}>
        <NewsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const lastUrl = () => String(fetchMock.mock.calls.at(-1)?.[0]);

beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("NewsPage", () => {
  it("por defecto pide solo las noticias que afectan a la cartera elegida", async () => {
    serveNews(ALL);
    renderPage();
    expect(screen.getByRole("heading", { level: 1, name: "Noticias" })).toBeTruthy();
    expect(await screen.findAllByRole("article")).toHaveLength(2);
    expect(lastUrl()).toContain("/api/v1/portfolios/laura/news?affecting=true");
    expect(screen.getByRole("button", { name: "Te afectan" }).getAttribute("aria-pressed")).toBe(
      "true",
    );
    expect(document.querySelector(".news-page-layout")?.className).toContain("w-full");
    // El aviso va al final como párrafo, sin tarjeta.
    expect(screen.getByText("No es asesoramiento.").closest("p")?.className).not.toMatch(/border/);
  });

  it("cada card enseña cómo afecta al dinero y abre el detalle; Escape lo cierra y vuelve a la card", async () => {
    serveNews(ALL);
    renderPage();
    const card = await screen.findByRole("article", { name: estimated.title });
    expect(card.textContent).toMatch(/Cómo afecta a tu dinero/);
    expect(card.textContent).toMatch(/entre -270\s€ y -110\s€/);
    // En la card no van el porcentaje ni el método: eso está en el detalle.
    expect(card.textContent).not.toMatch(/Equivale a/);
    expect(card.querySelector("svg[data-news-art]")).not.toBeNull();
    expect(card.querySelector("[data-news-status='estimated']")?.className).toContain(
      "bg-icon-gold-bg",
    );
    expect(card.querySelector("[data-news-value-tone='riesgo']")?.className).toContain(
      "text-trend-down",
    );

    const opener = screen.getByRole("button", { name: estimated.title });
    fireEvent.click(opener);
    const dialog = screen.getByRole("dialog", { name: estimated.title });
    expect(dialog.textContent).toMatch(/Cómo afecta a tu cartera/);
    expect(dialog.textContent).toMatch(/Equivale a/);
    const closeButton = screen.getByRole("button", { name: "Cerrar noticia" });
    expect(document.activeElement).toBe(closeButton);
    expect(closeButton.textContent).toBe("");
    expect(closeButton.querySelector("svg")).not.toBeNull();

    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    await waitFor(() => expect(document.activeElement).toBe(opener));
  });

  it("«Todas» incluye las que no afectan, y una categoría filtra", async () => {
    serveNews(ALL);
    renderPage();
    await screen.findAllByRole("article");
    fireEvent.click(screen.getByRole("button", { name: "Todas" }));
    await waitFor(() => expect(screen.getAllByRole("article")).toHaveLength(3));
    expect(lastUrl()).toContain("affecting=false");

    fireEvent.click(screen.getByRole("button", { name: "Resultados" }));
    await waitFor(() => expect(screen.getAllByRole("article")).toHaveLength(1));
    expect(lastUrl()).toContain("category=earnings");
    const categoryChip = screen.getByRole("button", { name: "Resultados" });
    expect(categoryChip.getAttribute("aria-pressed")).toBe("true");
    expect(categoryChip.className).toContain("aria-pressed:bg-accent");
    expect(categoryChip.querySelector("svg")?.className.baseVal).toContain("text-white");
  });

  it("filtra por fechas inclusivas y carga el límite disponible antes de filtrar", async () => {
    serveNews(ALL);
    renderPage();
    await screen.findAllByRole("article");

    fireEvent.click(screen.getByRole("button", { name: "Fecha" }));
    fireEvent.change(screen.getByLabelText("Desde"), { target: { value: "2025-02-26" } });
    fireEvent.change(screen.getByLabelText("Hasta"), { target: { value: "2025-02-26" } });

    await waitFor(() => {
      expect(lastUrl()).toContain("limit=200");
      expect(screen.getAllByRole("article")).toHaveLength(1);
    });
    expect(screen.getByRole("button", { name: "Fechas activas" })).toBeTruthy();
    expect(screen.getByRole("article", { name: estimated.title })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Limpiar fechas" }));
    await waitFor(() => {
      expect(lastUrl()).toContain("limit=30");
      expect(screen.getAllByRole("article")).toHaveLength(2);
    });
  });

  it("permite avanzar y retroceder por categorías con botones laterales", async () => {
    serveNews(ALL);
    renderPage();
    const rail = screen.getByRole("region", { name: "Filtros de noticias" });
    Object.defineProperty(rail, "clientWidth", { configurable: true, value: 250 });
    Object.defineProperty(rail, "scrollWidth", { configurable: true, value: 900 });
    const scrollBy = vi.fn();
    Object.defineProperty(rail, "scrollBy", { configurable: true, value: scrollBy });
    fireEvent(window, new Event("resize"));

    const next = screen.getByRole<HTMLButtonElement>("button", {
      name: "Desplazar filtros a la derecha",
    });
    await waitFor(() => expect(next.disabled).toBe(false));
    fireEvent.click(next);
    expect(scrollBy).toHaveBeenCalledWith({ left: 180, behavior: "smooth" });

    Object.defineProperty(rail, "scrollLeft", { configurable: true, value: 200 });
    fireEvent.scroll(rail);
    const previous = screen.getByRole<HTMLButtonElement>("button", {
      name: "Desplazar filtros a la izquierda",
    });
    await waitFor(() => expect(previous.disabled).toBe(false));
    fireEvent.click(previous);
    expect(scrollBy).toHaveBeenLastCalledWith({ left: -180, behavior: "smooth" });
  });

  it("sin noticias, lo explica según el filtro", async () => {
    serveNews([]);
    renderPage();
    expect(
      await screen.findByText("Ahora mismo no hay noticias que afecten a esta cartera."),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Divisas" }));
    expect(
      await screen.findByText("Ahora mismo no hay noticias de divisas que afecten a esta cartera."),
    ).toBeTruthy();
  });

  it("«Ver más noticias» pide la página siguiente", async () => {
    const many = Array.from({ length: 30 }, (_, i) => ({
      ...(estimated as NewsItemOut),
      id: `news_${i}`,
    }));
    serveNews(many);
    renderPage();
    expect(await screen.findAllByRole("article")).toHaveLength(30);
    expect(lastUrl()).toContain("limit=30");
    fireEvent.click(screen.getByRole("button", { name: "Ver más noticias" }));
    await waitFor(() => expect(lastUrl()).toContain("limit=60"));
  });

  it("si la API falla, no inventa nada", async () => {
    fetchMock.mockResolvedValue(new Response("{}", { status: 503 }));
    renderPage();
    expect(await screen.findByText(/no podemos mostrar las noticias/)).toBeTruthy();
    expect(screen.queryByRole("article")).toBeNull();
  });
});
