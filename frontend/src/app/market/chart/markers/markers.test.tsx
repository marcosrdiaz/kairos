import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import bce from "../../../../api/mocks/EventImpactOut.json";
import history from "../../../../api/mocks/PortfolioHistoryOut.json";
import type { EventImpactOut, PortfolioHistoryOut } from "../../../../api/generated/schema";
import { HistoryTable } from "../HistoryTable";
import { EventMarkerDot } from "./EventMarkerDot";
import { MarkerCard } from "./MarkerCard";
import { createMarkerStore } from "./markerStore";
import type { EventMarker } from "./placeMarkers";

afterEach(cleanup);

const MARKER: EventMarker = {
  event: bce as EventImpactOut,
  marketDate: "2025-06-05T12:15:00Z",
  date: "2026-11-06T00:00:00Z",
  value: 34311.68,
};

describe("marcador de noticia", () => {
  it("se enfoca con Tab y anuncia título, fecha real, impacto y confianza", () => {
    const store = createMarkerStore();
    render(
      <svg>
        <EventMarkerDot cx={100} cy={120} marker={MARKER} store={store} cardId="tarjeta" />
      </svg>,
    );
    const dot = screen.getByRole("button");
    expect(dot.getAttribute("tabindex")).toBe("0");
    expect(dot.getAttribute("aria-describedby")).toBe("tarjeta");
    expect(dot.getAttribute("aria-label")).toMatch(
      /^Noticia del 5 de junio de 2025: El BCE baja los tipos 0,25 puntos\. Impacto estimado en tu cartera entre [-−]10\s€ y 190\s€, confianza media\.$/,
    );
  });

  it("con el foco abre la tarjeta, Escape la cierra y las flechas no llegan a la gráfica", () => {
    const store = createMarkerStore();
    const onChartKey = vi.fn();
    render(
      <svg onKeyDown={onChartKey}>
        <EventMarkerDot cx={100} cy={120} marker={MARKER} store={store} cardId="tarjeta" />
      </svg>,
    );
    const dot = screen.getByRole("button");
    fireEvent.focus(dot);
    expect(store.get()?.marker.event.event_id).toBe("bce-2025-06");
    fireEvent.keyDown(dot, { key: "ArrowLeft" });
    expect(onChartKey).not.toHaveBeenCalled();
    fireEvent.keyDown(dot, { key: "Escape" });
    expect(store.get()).toBeNull();
  });
});

describe("tarjeta de la noticia", () => {
  it("muestra tipo y fecha real, título, mercado de ese día e impacto con rango y confianza", () => {
    const store = createMarkerStore();
    render(<MarkerCard store={store} id="tarjeta" width={800} />);
    const card = screen.getByRole("tooltip", { hidden: true });
    expect(card.hidden).toBe(true);
    act(() => store.set({ marker: MARKER, x: 200, y: 80 }));
    expect(card.hidden).toBe(false);
    const text = card.textContent ?? "";
    expect(text).toMatch(/Banco central · 5 de junio de 2025/);
    expect(text).toMatch(/El BCE baja los tipos 0,25 puntos/);
    expect(text).toMatch(/El mercado ese día/);
    expect(text).toMatch(/Petróleo.*\+0,74\s%/);
    expect(text).toMatch(/Tecnológicas de EE\. UU\..*−0,80\s%/);
    expect(text).toMatch(/entre [-−]10\s€ y 190\s€.*Confianza media/);
    expect(text).toMatch(/De dónde sale/);
    expect(card.querySelector("[data-calc-id]")?.getAttribute("data-calc-id")).toBe(bce.calc_id);
  });

  it("no se sale por la derecha", () => {
    const store = createMarkerStore();
    render(<MarkerCard store={store} id="tarjeta" width={500} />);
    act(() => store.set({ marker: MARKER, x: 490, y: 80 }));
    expect(screen.getByRole("tooltip", { hidden: true }).style.left).toBe("180px");
  });
});

describe("tabla alternativa", () => {
  it("incluye la noticia en la fila de su cierre", () => {
    render(
      <HistoryTable history={history as PortfolioHistoryOut} periodName="Último mes" markers={[MARKER]} />,
    );
    fireEvent.click(screen.getByText(/^Ver tabla/));
    const details = document.querySelector("details") as HTMLDetailsElement;
    details.open = true;
    fireEvent(details, new Event("toggle"));
    const row = document.querySelector("tr.kchart-row");
    expect(row?.textContent).toMatch(/Banco central.*El BCE baja los tipos.*entre [-−]10\s€ y 190\s€.*5 de junio de 2025/);
  });
});
