import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "./App";

afterEach(cleanup);

function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("App", () => {
  it("muestra las 2 pestañas y el botón del asistente", () => {
    renderAt("/inicio");
    const nav = screen.getByRole("navigation", { name: "Secciones" });
    for (const name of ["Inicio", "Cartera"]) {
      expect(nav.querySelector(`a[href="/${name.toLowerCase()}"]`)).not.toBeNull();
    }
    expect(nav.querySelector('a[href="/pregunta"]')).toBeNull();
    const launcher = screen.getByRole("button", { name: /Abrir el asistente/ });
    expect(launcher.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(launcher);
    expect(launcher.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByRole("heading", { name: "Pregunta a Kairos" })).toBeTruthy();
  });
  it("redirige / a /inicio", () => {
    renderAt("/");
    expect(screen.getByRole("heading", { name: "Inicio" })).toBeTruthy();
  });
  it("/pregunta abre el asistente sobre Inicio; /panel va sin pestañas", () => {
    renderAt("/pregunta");
    expect(screen.getByRole("heading", { name: "Inicio" })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Abrir el asistente/ }).getAttribute("aria-expanded")).toBe("true");
    cleanup();
    renderAt("/panel");
    expect(screen.getByRole("heading", { name: "Panel de contexto" })).toBeTruthy();
    expect(screen.queryByRole("navigation", { name: "Secciones" })).toBeNull();
  });
});
