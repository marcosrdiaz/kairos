import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import LabPage from "./LabPage";

afterEach(cleanup);

function renderLab() {
  return render(
    <MemoryRouter>
      <LabPage />
    </MemoryRouter>,
  );
}

describe("LabPage", () => {
  it("cada componente lleva su veredicto frente a DESIGN.md y un motivo", () => {
    renderLab();
    const headings = screen.getAllByRole("heading", { level: 2 });
    expect(headings).toHaveLength(8);
    for (const heading of headings) {
      const section = heading.closest("section");
      expect(section, heading.textContent ?? "").not.toBeNull();
      const verdict = within(section as HTMLElement).queryByText(/^(Encaja|Choca) con DESIGN\.md$/);
      expect(verdict, heading.textContent ?? "").not.toBeNull();
    }
  });

  it("solo quedan los componentes que ha aceptado el equipo", () => {
    renderLab();
    const titles = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(titles).toEqual([
      "Línea con banda de rango",
      "Sparklines",
      "Tarjeta de cifra con periodos",
      "Estado de las fuentes",
      "Barra de progreso frente a una regla",
      "Pestañas con indicador deslizante",
      "Pasos de un proceso",
      "Cambio suave de frase",
    ]);
  });

  it("pone primero la banda de rango y los sparklines", () => {
    renderLab();
    const titles = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(titles.slice(0, 2)).toEqual(["Línea con banda de rango", "Sparklines"]);
  });

  it("la banda ofrece una tabla con el rango de cada punto estimado", () => {
    renderLab();
    const table = screen.getByRole("table", { name: /6 meses observados y 4 estimados/ });
    expect(within(table).getAllByText("Estimado")).toHaveLength(4);
    expect(within(table).getAllByText("Observado")).toHaveLength(6);
  });

  it("las pestañas cambian con las flechas y mantienen una sola pestaña seleccionada", () => {
    renderLab();
    const list = screen.getByRole("tablist", { name: "Secciones de ejemplo" });
    const [first, second] = within(list).getAllByRole("tab");
    expect(first?.getAttribute("aria-selected")).toBe("true");
    fireEvent.keyDown(list, { key: "ArrowRight" });
    expect(second?.getAttribute("aria-selected")).toBe("true");
    expect(first?.getAttribute("aria-selected")).toBe("false");
  });

  it("los pasos no avanzan solos: solo al pulsar el botón", () => {
    renderLab();
    const steps = screen.getByRole("list", { name: "Pasos de ejemplo" });
    expect(within(steps).getAllByText(/En curso/)).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Siguiente paso" }));
    expect(within(steps).getAllByText(/Hecho/)).toHaveLength(2);
  });
});
