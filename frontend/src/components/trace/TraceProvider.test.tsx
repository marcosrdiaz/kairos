import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import type { TraceOut } from "../../api/generated/schema";
import traceMock from "../../api/mocks/TraceOut.json";
import { TraceDialog } from "./TraceDialog";
import { TraceFigure } from "./TraceFigure";
import { TraceLink } from "./TraceLink";
import { TraceProvider } from "./TraceProvider";
import { TRACE_KIND_HOW, TRACE_KIND_LABEL } from "./labels";

const ROOT = { ...(traceMock as unknown as TraceOut), calc_id: "calc_root" };

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function stubTraces(traces: TraceOut[]) {
  const byId = new Map(traces.map((t) => [t.calc_id, t]));
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const found = byId.get(url.split("/").pop() ?? "");
      return found ? json(found) : json({ code: "NOT_FOUND", details: {} }, 404);
    }),
  );
}

function renderWithProvider(ui: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <TraceProvider>{ui}</TraceProvider>
    </QueryClientProvider>,
  );
}

/** La cifra abre su tarjeta (T5-18) y la tarjeta, la hoja con la traza entera. */
async function openFull(name: RegExp | string) {
  fireEvent.click(screen.getByRole("button", { name }));
  const card = await screen.findByRole("group", { name: "De dónde sale esta cifra" });
  fireEvent.click(await within(card).findByRole("button", { name: "Ver el cálculo completo" }));
  return screen.findByRole("dialog", { hidden: true });
}

async function openFigure() {
  renderWithProvider(<TraceFigure calcId="calc_root">100 €</TraceFigure>);
  return openFull(/De dónde sale/);
}

beforeEach(() => {
  // jsdom no siempre implementa los métodos modales de <dialog>.
  HTMLDialogElement.prototype.showModal = function showModal() {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function close() {
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  };
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("TraceFigure y TraceLink", () => {
  it("sin calc_id, la cifra se pinta sin botón", () => {
    renderWithProvider(<TraceFigure calcId={null}>100 €</TraceFigure>);
    expect(screen.getByText("100 €")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("fuera del provider, la cifra conserva data-calc-id y no hay enlace", () => {
    const { container } = render(
      <>
        <TraceFigure calcId="calc_root">100 €</TraceFigure>
        <TraceLink calcId="calc_root" />
      </>,
    );
    expect(container.querySelector('span[data-calc-id="calc_root"]')).not.toBeNull();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("TraceLink lleva a la misma hoja", async () => {
    stubTraces([ROOT]);
    renderWithProvider(<TraceLink calcId="calc_root" />);
    const dialog = await openFull("¿De dónde sale?");
    expect(await within(dialog).findByText("Fórmula")).toBeTruthy();
  });
});

describe("TraceDialog", () => {
  it("muestra entradas, fórmula, resultado, fuentes y fecha", async () => {
    stubTraces([ROOT]);
    const dialog = await openFigure();
    const view = within(dialog);
    expect(await view.findByText(TRACE_KIND_LABEL.valuation)).toBeTruthy();
    for (const title of ["Entradas", "Fórmula", "Resultado", "Fuentes", "Fecha del cálculo"]) {
      expect(view.getByRole("heading", { name: title, hidden: true })).toBeTruthy();
    }
    expect(view.getByText(ROOT.formula)).toBeTruthy();
    expect(view.getByText(/34\.311,68/)).toBeTruthy();
    expect(view.getByText("Precio iShares Core MSCI World")).toBeTruthy();
  });

  it("pide y muestra los cálculos de origen", async () => {
    stubTraces([
      { ...ROOT, parent_calc_ids: ["calc_parent"] },
      { ...ROOT, calc_id: "calc_parent", kind: "exposure", parent_calc_ids: [] },
    ]);
    const dialog = await openFigure();
    expect(await within(dialog).findByText(TRACE_KIND_LABEL.exposure)).toBeTruthy();
  });

  it("arriba dice qué cálculo es, cuándo se hizo y cuántas fuentes tiene", async () => {
    stubTraces([ROOT]);
    const dialog = await openFigure();
    const summary = (await within(dialog).findByText(/^Calculado el/)).textContent ?? "";
    const n = ROOT.sources.length;
    expect(summary).toContain(`${n} ${n === 1 ? "fuente" : "fuentes"}`);
  });

  it("los cálculos de origen son pasos numerados y en orden, también para el lector", async () => {
    stubTraces([
      { ...ROOT, parent_calc_ids: ["calc_a", "calc_falta"] },
      { ...ROOT, calc_id: "calc_a", kind: "exposure", parent_calc_ids: [] },
    ]);
    const dialog = await openFigure();
    await within(dialog).findByText(TRACE_KIND_LABEL.exposure);
    const steps = within(dialog).getAllByRole("listitem", { hidden: true }).filter((li) =>
      li.classList.contains("trace-step"),
    );
    expect(steps).toHaveLength(2);
    expect(steps[0]?.closest("ol")).not.toBeNull();
    expect(steps[0]?.textContent).toMatch(/^1Paso 1: /);
    expect(steps[1]?.textContent).toMatch(/^2Paso 2: Traza no disponible/);
  });

  it("explica la fórmula en palabras y deja la exacta plegada", async () => {
    stubTraces([ROOT]);
    const dialog = await openFigure();
    expect(await within(dialog).findByText(TRACE_KIND_HOW.valuation)).toBeTruthy();
    const exact = within(dialog).getByText(ROOT.formula);
    const details = exact.closest("details");
    expect(details).not.toBeNull();
    expect(details?.open).toBe(false);
    expect(within(dialog).getByText("Ver la fórmula exacta")).toBeTruthy();
  });

  it("es un modal centrado sin JSON a la vista", async () => {
    stubTraces([ROOT]);
    const dialog = await openFigure();
    await within(dialog).findByText(ROOT.formula);
    expect(dialog.className).toContain("trace-dialog");
    expect(dialog.className).toContain("sm:m-auto");
    expect(dialog.className).not.toContain("ml-auto");
    expect(dialog.textContent).not.toMatch(/[{}"]\s*\w+"\s*:/);
  });

  it("un origen que no existe se muestra como no disponible, sin romper la traza", async () => {
    stubTraces([{ ...ROOT, parent_calc_ids: ["calc_falta"] }]);
    const dialog = await openFigure();
    expect(await within(dialog).findByText("Traza no disponible")).toBeTruthy();
    expect(within(dialog).getByText(ROOT.formula)).toBeTruthy();
  });

  it("un 404 de la cifra se explica como traza no disponible", async () => {
    // La tarjeta no ofrece la hoja sin traza; la hoja se prueba sola por si se abre igualmente.
    stubTraces([]);
    renderWithProvider(<TraceDialog calcId="calc_root" onClose={() => undefined} />);
    const dialog = await screen.findByRole("dialog", { hidden: true });
    expect(await within(dialog).findByText(/Traza no disponible/)).toBeTruthy();
    expect(within(dialog).queryByRole("alert", { hidden: true })).toBeNull();
  });

  it("un error del servidor ofrece reintentar", async () => {
    const fetchMock = vi.fn(async () => json({ code: "INTERNAL" }, 500));
    vi.stubGlobal("fetch", fetchMock);
    const dialog = await openFigure();
    const retry = await within(dialog).findByRole("button", { name: "Reintentar", hidden: true });
    fetchMock.mockImplementation(async () => json(ROOT));
    fireEvent.click(retry);
    expect(await within(dialog).findByText(ROOT.formula)).toBeTruthy();
  });

  it("el botón Cerrar desmonta la hoja", async () => {
    stubTraces([ROOT]);
    const dialog = await openFigure();
    fireEvent.click(within(dialog).getByRole("button", { name: "Cerrar", hidden: true }));
    await waitFor(() => expect(screen.queryByRole("dialog", { hidden: true })).toBeNull());
  });

  it("un clic en el fondo cierra y uno en el contenido no", async () => {
    stubTraces([ROOT]);
    const dialog = await openFigure();
    fireEvent.click(await within(dialog).findByText("Fórmula"));
    expect(screen.queryByRole("dialog", { hidden: true })).not.toBeNull();
    fireEvent.click(dialog);
    await waitFor(() => expect(screen.queryByRole("dialog", { hidden: true })).toBeNull());
  });
});
