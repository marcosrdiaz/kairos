import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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
    vi.fn(async () => new Response("[]", { status: 200, headers: { "Content-Type": "application/json" } })),
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
  it("monta el alta, las operaciones y las aportaciones periódicas", async () => {
    renderPage();
    for (const name of ["Registrar una operación", "Aportaciones periódicas"]) {
      expect(screen.getByRole("heading", { level: 2, name, hidden: true })).toBeTruthy();
    }
    expect(screen.getByRole("heading", { level: 2, name: /Añadir posiciones/, hidden: true })).toBeTruthy();
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

  it("muestra una sección cada vez, empezando por Operaciones", () => {
    renderPage();
    expect(screen.getAllByRole("tab").map((t) => t.textContent)).toEqual([
      "Operaciones",
      "Aportaciones periódicas",
      "Añadir posiciones",
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
    fireEvent.keyDown(document.activeElement as Element, { key: "End" });
    expect(document.activeElement).toBe(tab("Añadir posiciones"));
    expect(tab("Añadir posiciones").getAttribute("aria-selected")).toBe("true");
    fireEvent.keyDown(document.activeElement as Element, { key: "Home" });
    expect(document.activeElement).toBe(tab("Operaciones"));
    fireEvent.keyDown(document.activeElement as Element, { key: "ArrowLeft" });
    expect(document.activeElement).toBe(tab("Añadir posiciones"));
  });

  it("no pierde un formulario a medias al cambiar de pestaña", () => {
    renderPage();
    const amount = screen.getByRole("textbox", { name: /Importe/ }) as HTMLInputElement;
    fireEvent.change(amount, { target: { value: "250" } });
    fireEvent.click(tab("Añadir posiciones"));
    fireEvent.click(tab("Operaciones"));
    expect((screen.getByRole("textbox", { name: /Importe/ }) as HTMLInputElement).value).toBe("250");
  });
});
