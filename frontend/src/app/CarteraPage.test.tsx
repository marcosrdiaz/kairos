import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CarteraPage } from "./CarteraPage";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function renderPage() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const body =
        String(input) === "/api/v1/portfolios"
          ? [{ id: "laura", name: "Laura", kind: "personal", risk_profile: "moderado", profile: "moderado" }]
          : [];
      return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
    }),
  );
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/cartera?p=laura"]}>
        <CarteraPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const tab = (name: string) => screen.getByRole("tab", { name });

describe("CarteraPage", () => {
  it("monta las operaciones y las aportaciones periódicas, sin el alta de posiciones", async () => {
    renderPage();
    for (const name of ["Registrar una operación", "Aportaciones periódicas"]) {
      expect(screen.getByRole("heading", { level: 2, name, hidden: true })).toBeTruthy();
    }
    expect(screen.queryByRole("heading", { level: 2, name: /Añadir posiciones/, hidden: true })).toBeNull();
    expect(await screen.findByText("Esta cartera aún no tiene ningún plan de aportaciones.")).toBeTruthy();
  });

  it("deja el selector de carteras fuera de las pestañas, arriba", () => {
    renderPage();
    const carteras = screen.getByRole("heading", { level: 2, name: "Carteras" });
    const tablist = screen.getByRole("tablist", { name: "Secciones de la cartera" });
    expect(carteras.compareDocumentPosition(tablist) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(tablist.contains(carteras)).toBe(false);
    expect(screen.getByRole("tabpanel").contains(carteras)).toBe(false);
  });

  it("agrupa el selector y la gestión de carteras en el contenedor inicial", async () => {
    renderPage();
    const portfolios = screen.getByRole("region", { name: "Carteras" });
    expect(await within(portfolios).findByRole("button", { name: "Nueva cartera" })).toBeTruthy();
    expect(await within(portfolios).findByRole("button", { name: "Renombrar «Laura»" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Tus carteras" })).toBeNull();
  });

  it("no ofrece cargar las carteras de ejemplo", () => {
    renderPage();
    expect(screen.queryByRole("button", { name: /carteras de ejemplo/i, hidden: true })).toBeNull();
  });

  it("muestra una sección cada vez, empezando por Operaciones", () => {
    renderPage();
    expect(screen.getAllByRole("tab").map((t) => t.textContent)).toEqual([
      "Operaciones",
      "Aportaciones periódicas",
    ]);
    expect(tab("Operaciones").getAttribute("aria-selected")).toBe("true");
    expect(screen.getByRole("heading", { level: 2, name: "Registrar una operación" })).toBeTruthy();
    expect(screen.queryByRole("heading", { level: 2, name: "Aportaciones periódicas" })).toBeNull();

    fireEvent.click(tab("Aportaciones periódicas"));
    expect(screen.getByRole("heading", { level: 2, name: "Aportaciones periódicas" })).toBeTruthy();
    expect(screen.queryByRole("heading", { level: 2, name: "Registrar una operación" })).toBeNull();
  });

  it("se mueve con flechas, Inicio y Fin", () => {
    renderPage();
    const first = tab("Operaciones");
    first.focus();
    fireEvent.keyDown(first, { key: "ArrowRight" });
    expect(document.activeElement).toBe(tab("Aportaciones periódicas"));
    fireEvent.keyDown(document.activeElement as Element, { key: "Home" });
    expect(document.activeElement).toBe(tab("Operaciones"));
    fireEvent.keyDown(document.activeElement as Element, { key: "End" });
    expect(document.activeElement).toBe(tab("Aportaciones periódicas"));
    expect(tab("Aportaciones periódicas").getAttribute("aria-selected")).toBe("true");
    fireEvent.keyDown(document.activeElement as Element, { key: "ArrowRight" });
    expect(document.activeElement).toBe(tab("Operaciones"));
  });

  it("no pierde un formulario a medias al cambiar de pestaña", () => {
    renderPage();
    const amount = screen.getByRole("textbox", { name: /Importe/ }) as HTMLInputElement;
    fireEvent.change(amount, { target: { value: "250" } });
    fireEvent.click(tab("Aportaciones periódicas"));
    fireEvent.click(tab("Operaciones"));
    expect((screen.getByRole("textbox", { name: /Importe/ }) as HTMLInputElement).value).toBe("250");
  });
});
