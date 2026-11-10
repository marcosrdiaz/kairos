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
    expect(screen.getByText("Información, no asesoramiento")).toBeTruthy();
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
    expect(screen.getByRole("button", { name: "Resultados" }).getAttribute("aria-pressed")).toBe(
      "true",
    );
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

  it("si la API falla, no inventa nada", async () => {
    fetchMock.mockResolvedValue(new Response("{}", { status: 503 }));
    renderPage();
    expect(await screen.findByText(/no podemos mostrar las noticias/)).toBeTruthy();
    expect(screen.queryByRole("article")).toBeNull();
  });
});
