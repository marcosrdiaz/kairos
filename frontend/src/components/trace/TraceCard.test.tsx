import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { TraceOut } from "../../api/generated/schema";
import traceMock from "../../api/mocks/TraceOut.json";
import { TraceFigure } from "./TraceFigure";
import { TraceLink } from "./TraceLink";
import { TraceProvider } from "./TraceProvider";
import { TRACE_KIND_LABEL } from "./labels";

const ROOT = { ...(traceMock as unknown as TraceOut), calc_id: "calc_root" };
const CARD = { name: "De dónde sale esta cifra" } as const;

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

function renderFigure() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <TraceProvider>
        <p>
          Vale <TraceFigure calcId="calc_root">100 €</TraceFigure> hoy.
        </p>
        <button type="button">Fuera</button>
      </TraceProvider>
    </QueryClientProvider>,
  );
  return screen.getByRole("button", { name: /De dónde sale/ });
}

const card = () => screen.queryByRole("group", CARD);

beforeEach(() => {
  stubTraces([ROOT]);
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

describe("Tarjeta de una cifra", () => {
  it("al pasar el ratón muestra valor, explicación, fecha y fuente", async () => {
    const figure = renderFigure();
    expect(card()).toBeNull();
    fireEvent.pointerEnter(figure, { pointerType: "mouse" });
    const open = await screen.findByRole("group", CARD);
    const view = within(open);
    expect(view.getByText("100 €")).toBeTruthy();
    expect(await view.findByText(TRACE_KIND_LABEL.valuation)).toBeTruthy();
    expect(open.textContent).toMatch(/Calculado el \d/);
    expect(view.getByText("Precio iShares Core MSCI World")).toBeTruthy();
    expect(figure.getAttribute("aria-expanded")).toBe("true");
  });

  it("no se cierra al llevar el ratón a la tarjeta y sí al salir de ella", async () => {
    const figure = renderFigure();
    fireEvent.pointerEnter(figure, { pointerType: "mouse" });
    const open = await screen.findByRole("group", CARD);
    fireEvent.pointerLeave(figure, { pointerType: "mouse" });
    fireEvent.pointerEnter(open, { pointerType: "mouse" });
    await act(() => new Promise((resolve) => setTimeout(resolve, 300)));
    expect(card()).not.toBeNull();
    fireEvent.pointerLeave(open, { pointerType: "mouse" });
    await waitFor(() => expect(card()).toBeNull());
  });

  it("un toque no la abre por hover: la abre el clic", async () => {
    const figure = renderFigure();
    fireEvent.pointerEnter(figure, { pointerType: "touch" });
    await act(() => new Promise((resolve) => setTimeout(resolve, 300)));
    expect(card()).toBeNull();
    fireEvent.click(figure);
    expect(await screen.findByRole("group", CARD)).toBeTruthy();
  });

  it("con el foco se abre, el lector la recibe como descripción y Esc la cierra", async () => {
    const figure = renderFigure();
    act(() => figure.focus());
    const open = await screen.findByRole("group", CARD);
    await within(open).findByText(TRACE_KIND_LABEL.valuation);
    const described = document.getElementById(figure.getAttribute("aria-describedby") ?? "");
    expect(described?.textContent).toMatch(TRACE_KIND_LABEL.valuation);
    expect(described?.textContent).toMatch("Precio iShares Core MSCI World");
    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => expect(card()).toBeNull());
    expect(document.activeElement).toBe(figure);
  });

  it("el clic la fija: no se cierra al salir con el ratón y sí al pulsar fuera", async () => {
    const figure = renderFigure();
    fireEvent.pointerEnter(figure, { pointerType: "mouse" });
    fireEvent.click(figure);
    await screen.findByRole("group", CARD);
    fireEvent.pointerLeave(figure, { pointerType: "mouse" });
    await act(() => new Promise((resolve) => setTimeout(resolve, 300)));
    expect(card()).not.toBeNull();
    fireEvent.pointerDown(screen.getByRole("button", { name: "Fuera" }));
    await waitFor(() => expect(card()).toBeNull());
  });

  it("un segundo clic la cierra", async () => {
    const figure = renderFigure();
    fireEvent.click(figure);
    await screen.findByRole("group", CARD);
    fireEvent.click(figure);
    await waitFor(() => expect(card()).toBeNull());
  });

  it("«Ver el cálculo completo» abre la hoja con la traza entera", async () => {
    const figure = renderFigure();
    fireEvent.click(figure);
    const open = await screen.findByRole("group", CARD);
    fireEvent.click(await within(open).findByRole("button", { name: "Ver el cálculo completo" }));
    const sheet = await screen.findByRole("dialog", { hidden: true });
    expect(await within(sheet).findByText("Fórmula")).toBeTruthy();
    await waitFor(() => expect(card()).toBeNull());
  });

  it("sin traza guardada lo dice y no ofrece el cálculo completo", async () => {
    stubTraces([]);
    const figure = renderFigure();
    fireEvent.click(figure);
    const open = await screen.findByRole("group", CARD);
    expect(await within(open).findByText(/Traza no disponible/)).toBeTruthy();
    expect(within(open).queryByRole("button", { name: "Ver el cálculo completo" })).toBeNull();
  });

  it("cerrada no deja texto en el DOM (la cifra aparece una sola vez)", () => {
    renderFigure();
    expect(screen.getAllByText("100 €")).toHaveLength(1);
  });

  it("TraceLink abre la misma tarjeta, sin cifra", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <TraceProvider>
          <TraceLink calcId="calc_root" />
        </TraceProvider>
      </QueryClientProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: "¿De dónde sale?" }));
    const open = await screen.findByRole("group", CARD);
    expect(await within(open).findByText(TRACE_KIND_LABEL.valuation)).toBeTruthy();
  });
});
