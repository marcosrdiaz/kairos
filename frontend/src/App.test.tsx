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
  it("muestra las cinco rutas integradas y el botón del asistente", () => {
    renderAt("/inicio");
    const nav = screen.getByRole("navigation", { name: "Secciones" });
    for (const [name, path] of [["Inicio", "/inicio"], ["Cartera", "/cartera"], ["Noticias", "/noticias"], ["Avisos", "/alertas"], ["Panel de contexto", "/panel"]]) {
      expect(nav.querySelector(`a[href="${path}"]`)?.textContent).toContain(name);
    }
    expect(nav.querySelector('a[href="/pregunta"]')).toBeNull();
    const launcher = screen.getByRole("button", { name: /Abrir el asistente/ });
    expect(launcher.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(launcher);
    expect(launcher.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByRole("heading", { name: "Pregunta a Kairos" })).toBeTruthy();
  });
  it("todas las pantallas llevan el aviso de IA y un enlace para saltar al contenido", () => {
    for (const path of ["/inicio", "/cartera", "/alertas"]) {
      renderAt(path);
      expect(screen.getByText(/usa inteligencia artificial.*No es asesoramiento financiero/)).toBeTruthy();
      const skip = screen.getByRole("link", { name: "Saltar al contenido" });
      expect(skip.getAttribute("href")).toBe("#contenido");
      expect(document.getElementById("contenido")?.tabIndex).toBe(-1);
      cleanup();
    }
    renderAt("/panel");
    expect(screen.getByRole("region", { name: "Información, no asesoramiento" })).toBeTruthy();
  });
  it("redirige / a /inicio", () => {
    renderAt("/");
    expect(screen.getByRole("heading", { name: "Inicio" })).toBeTruthy();
  });
  it("Avisos cambia el contenido sin abrir un diálogo y conserva el asistente", () => {
    renderAt("/inicio");
    fireEvent.click(screen.getByRole("link", { name: "Avisos" }));
    expect(screen.getByRole("heading", { level: 1, name: "Avisos" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Avisos" }).getAttribute("aria-current")).toBe("page");
    expect(screen.queryByRole("dialog", { name: "Avisos" })).toBeNull();
    expect(screen.getByRole("button", { name: /Abrir el asistente/ })).toBeTruthy();
  });
  it("/pregunta abre el asistente sobre Inicio; /panel conserva la navegación y el chatbot", () => {
    renderAt("/pregunta");
    expect(screen.getByRole("heading", { name: "Inicio" })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Abrir el asistente/ }).getAttribute("aria-expanded")).toBe("true");
    cleanup();
    renderAt("/panel");
    expect(screen.getByRole("heading", { name: "Panel de contexto" })).toBeTruthy();
    expect(screen.getByRole("navigation", { name: "Secciones" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Panel de contexto" }).getAttribute("aria-current")).toBe("page");
    expect(screen.getByRole("button", { name: /Abrir el asistente/ })).toBeTruthy();
    expect(screen.queryByRole("radio", { name: "Laura" })).toBeNull();
  });
});
