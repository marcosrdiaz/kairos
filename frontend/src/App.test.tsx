import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { App } from "./App";

afterEach(cleanup);

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("App", () => {
  it("muestra las 3 pestañas", () => {
    renderAt("/inicio");
    const nav = screen.getByRole("navigation", { name: "Secciones" });
    for (const name of ["Inicio", "Cartera", "Pregunta"]) {
      expect(nav.querySelector(`a[href="/${name.toLowerCase()}"]`)).not.toBeNull();
    }
  });
  it("redirige / a /inicio", () => {
    renderAt("/");
    expect(screen.getByRole("heading", { name: "Inicio" })).toBeTruthy();
  });
  it("navega a /pregunta y a /panel (sin pestañas)", () => {
    renderAt("/pregunta");
    expect(screen.getByRole("heading", { name: "Pregunta" })).toBeTruthy();
    cleanup();
    renderAt("/panel");
    expect(screen.getByRole("heading", { name: "Panel de contexto" })).toBeTruthy();
    expect(screen.queryByRole("navigation", { name: "Secciones" })).toBeNull();
  });
});
