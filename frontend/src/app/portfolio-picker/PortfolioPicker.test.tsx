import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DemoReset } from "./DemoReset";
import { PortfolioPicker } from "./PortfolioPicker";

const PORTFOLIOS = [
  { id: "laura", name: "Laura", profile: "dinamico" },
  { id: "javier", name: "Javier", profile: "moderado" },
];

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function LocationProbe() {
  const { search } = useLocation();
  return <div data-testid="search">{search}</div>;
}

function renderWith(ui: React.ReactNode, path = "/cartera") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        {ui}
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("PortfolioPicker", () => {
  it("lista las carteras como radios y marca la de ?p=", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => json(PORTFOLIOS)));
    renderWith(<PortfolioPicker />, "/cartera?p=javier");
    const javier = await screen.findByRole("radio", { name: "Javier" });
    expect((javier as HTMLInputElement).checked).toBe(true);
    expect((screen.getByRole("radio", { name: "Laura" }) as HTMLInputElement).checked).toBe(false);
    expect(screen.getByRole("group", { name: "Cartera" })).toBeTruthy();
  });

  it("sin ?p= marca Laura (cartera del guion)", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => json(PORTFOLIOS)));
    renderWith(<PortfolioPicker />);
    const laura = await screen.findByRole("radio", { name: "Laura" });
    expect((laura as HTMLInputElement).checked).toBe(true);
  });

  it("elegir una cartera la guarda en ?p= y conserva el resto de la query", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => json(PORTFOLIOS)));
    renderWith(<PortfolioPicker />, "/cartera?p=laura&x=1");
    fireEvent.click(await screen.findByRole("radio", { name: "Javier" }));
    const search = new URLSearchParams(screen.getByTestId("search").textContent ?? "");
    expect(search.get("p")).toBe("javier");
    expect(search.get("x")).toBe("1");
  });

  it("si falla la API lo dice, sin inventar carteras", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => json({ code: "INTERNAL" }, 500)));
    renderWith(<PortfolioPicker />);
    expect(await screen.findByText(/no podemos cargar las carteras/)).toBeTruthy();
    expect(screen.queryByRole("radio")).toBeNull();
  });
});

describe("DemoReset", () => {
  it("pide confirmación, pone el foco en Cancelar y no llama a la API hasta confirmar", async () => {
    const fetchMock = vi.fn(async () => json({ portfolio_ids: ["laura", "javier"] }));
    vi.stubGlobal("fetch", fetchMock);
    renderWith(<DemoReset />);
    fireEvent.click(screen.getByRole("button", { name: "Cargar carteras de ejemplo" }));
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Cancelar" }));
    expect(fetchMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.getByRole("button", { name: "Cargar carteras de ejemplo" })).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("al confirmar hace POST /demo/reset con preload y lo anuncia", async () => {
    const fetchMock = vi.fn<(url: string, init?: RequestInit) => Promise<Response>>(async () =>
      json({ portfolio_ids: ["laura", "javier"], preloaded_event_ids: [] }),
    );
    vi.stubGlobal("fetch", fetchMock);
    renderWith(<DemoReset />);
    fireEvent.click(screen.getByRole("button", { name: "Cargar carteras de ejemplo" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Sí, restaurar" }));
    });
    await waitFor(() =>
      expect(screen.getByRole("status").textContent).toMatch(/estado inicial/),
    );
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("/api/v1/demo/reset");
    expect(init?.method).toBe("POST");
    expect(JSON.parse(init?.body as string)).toEqual({ preload: true });
  });

  it("sin modo demo explica por qué no se puede", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => json({ code: "DEMO_MODE_DISABLED", message: "", details: {} }, 403)),
    );
    renderWith(<DemoReset />);
    fireEvent.click(screen.getByRole("button", { name: "Cargar carteras de ejemplo" }));
    fireEvent.click(screen.getByRole("button", { name: "Sí, restaurar" }));
    expect(await screen.findByText(/solo está disponible en el modo demo/)).toBeTruthy();
  });
});
