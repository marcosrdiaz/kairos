import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CarteraPage } from "./CarteraPage";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("CarteraPage", () => {
  it("monta el alta, las operaciones y las aportaciones periódicas", async () => {
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
    for (const name of ["Registrar una operación", "Aportaciones periódicas"]) {
      expect(screen.getByRole("heading", { level: 2, name })).toBeTruthy();
    }
    expect(screen.getByRole("heading", { level: 2, name: /Añadir posiciones/ })).toBeTruthy();
    expect(await screen.findByText("Esta cartera aún no tiene ningún plan de aportaciones.")).toBeTruthy();
  });
});
