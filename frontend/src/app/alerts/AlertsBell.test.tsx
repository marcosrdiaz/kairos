import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import type { AlertOut, EventImpactOut } from "../../api/generated/schema";
import alertMock from "../../api/mocks/AlertOut.json";
import nvdaMock from "../../api/mocks/EventImpactOut.nvda.json";
import { TraceProvider } from "../../components/trace/TraceProvider";
import { AlertsBell } from "./AlertsBell";
import { markRead } from "./readStore";

const EVENT_ALERT = { ...(alertMock as AlertOut), event_id: (nvdaMock as EventImpactOut).event_id };
const MOVE_ALERT = {
  ...EVENT_ALERT,
  id: "alr_move",
  event_id: null,
  kind: "market_move",
  calc_id: "calc_move",
} as unknown as AlertOut; // `market_move` llega con T2-21; el frontend ya lo acepta

const IMPACT_CASES = [
  { label: "positivo", low: "120.00", high: "300.00", tone: "text-trend-up", hasArrow: true },
  { label: "negativo", low: "-620.00", high: "-320.00", tone: "text-trend-down", hasArrow: true },
  { label: "que cruza el cero", low: "-20.00", high: "30.00", tone: "text-ink", hasArrow: false },
] as const;

let alerts: AlertOut[] = [];
let events: EventImpactOut[] = [];
const fetchMock = vi.fn((input: RequestInfo | URL) => {
  const url = String(input);
  const body = url.includes("/alerts") ? alerts : url.includes("/events") ? events : {};
  return Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));
});

function renderBell(portfolio = "laura") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/inicio?p=${portfolio}`]}>
        <TraceProvider>
          <AlertsBell />
        </TraceProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const bell = () => screen.getByRole("button", { name: /^Avisos/ });

async function openInbox() {
  fireEvent.click(await screen.findByRole("button", { name: /sin leer/ }));
  return screen.findByRole("dialog", { name: "Avisos", hidden: true });
}

beforeEach(() => {
  localStorage.clear();
  events = [nvdaMock as EventImpactOut];
  vi.stubGlobal("fetch", fetchMock);
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

describe("AlertsBell", () => {
  it("sin avisos, lo dice en el nombre y no pinta globo", async () => {
    alerts = [];
    renderBell();
    await waitFor(() => expect(bell().getAttribute("aria-label")).toBe("Avisos, ninguno sin leer"));
    expect(screen.queryByTestId("alerts-badge")).toBeNull();
  });

  it("cuenta los no leídos en el globo y en el nombre accesible", async () => {
    alerts = [EVENT_ALERT, MOVE_ALERT];
    renderBell();
    await waitFor(() => expect(bell().getAttribute("aria-label")).toBe("Avisos, 2 sin leer"));
    expect(screen.getByTestId("alerts-badge").textContent).toBe("2");
  });

  it("los ya leídos en este navegador no cuentan", async () => {
    alerts = [EVENT_ALERT, MOVE_ALERT];
    markRead("laura", [EVENT_ALERT.id]);
    renderBell();
    await waitFor(() => expect(bell().getAttribute("aria-label")).toBe("Avisos, 1 sin leer"));
  });

  it("lista cada aviso con mensaje, rango, confianza y «¿De dónde sale?»", async () => {
    alerts = [EVENT_ALERT, MOVE_ALERT];
    renderBell();
    const dialog = await openInbox();
    const [eventItem, moveItem] = within(dialog).getAllByRole("article", { hidden: true });
    expect(within(eventItem!).getByText(EVENT_ALERT.message)).toBeTruthy();
    await waitFor(() => expect(eventItem!.querySelector(".tabular-nums")).not.toBeNull());
    const impactText = within(eventItem!).getByText(/Confianza (alta|media|baja)/);
    expect(impactText.textContent).toMatch(/entre -620\s€ y -320\s€/);
    expect(eventItem!.querySelector(".tabular-nums")?.className).toContain("text-trend-down");
    expect(eventItem!.getAttribute("data-calc-id")).toBe(EVENT_ALERT.calc_id);
    // `market_move`: sin evento, sin rango, pero con su tipo y su traza.
    expect(within(moveItem!).getByText("Movimiento de tu cartera")).toBeTruthy();
    expect(within(moveItem!).queryByText(/Impacto estimado/)).toBeNull();
    expect(within(moveItem!).getByRole("button", { name: "¿De dónde sale?", hidden: true })).toBeTruthy();
    expect(within(dialog).getByText(/no asesoramiento financiero/)).toBeTruthy();
  });

  it("marcar uno como leído baja el contador y lo guarda", async () => {
    alerts = [EVENT_ALERT, MOVE_ALERT];
    renderBell();
    const dialog = await openInbox();
    const [eventItem] = within(dialog).getAllByRole("article", { hidden: true });
    const markRead = within(eventItem!).getByRole("button", { name: "Marcar como leído", hidden: true });
    expect(markRead.className).toContain("min-h-touch");
    expect(markRead.className).toContain("rounded-control");
    expect(markRead.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
    fireEvent.click(markRead);
    expect(bell().getAttribute("aria-label")).toBe("Avisos, 1 sin leer");
    expect(within(eventItem!).queryByText("Nuevo")).toBeNull();
    expect(localStorage.getItem("kairos-alerts-read:laura")).toContain(EVENT_ALERT.id);
  });

  it("«Marcar todos como leídos» deja el contador a cero y desaparece", async () => {
    alerts = [EVENT_ALERT, MOVE_ALERT];
    renderBell();
    const dialog = await openInbox();
    const markAll = within(dialog).getByRole("button", { name: "Marcar todos como leídos", hidden: true });
    expect(markAll.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
    fireEvent.click(markAll);
    expect(bell().getAttribute("aria-label")).toBe("Avisos, ninguno sin leer");
    expect(within(dialog).queryByRole("button", { name: "Marcar todos como leídos", hidden: true })).toBeNull();
  });

  it.each(IMPACT_CASES)(
    "muestra el impacto $label con color semántico y sin depender solo del color",
    async ({ low, high, tone, hasArrow }) => {
      alerts = [EVENT_ALERT];
      events = [{ ...(nvdaMock as EventImpactOut), low_eur: low, high_eur: high }];
      renderBell();
      const dialog = await openInbox();
      const [item] = within(dialog).getAllByRole("article", { hidden: true });
      await waitFor(() => expect(item!.querySelector(".tabular-nums")).not.toBeNull());
      const range = item!.querySelector(".tabular-nums");
      expect(range?.className).toContain(tone);
      expect(range?.querySelector("svg") !== null).toBe(hasArrow);
    },
  );

  it("los leídos son de cada cartera", async () => {
    alerts = [EVENT_ALERT];
    markRead("javier", [EVENT_ALERT.id]);
    renderBell("laura");
    await waitFor(() => expect(bell().getAttribute("aria-label")).toBe("Avisos, 1 sin leer"));
  });

  it("se cierra con el botón y vuelve a la campana", async () => {
    alerts = [EVENT_ALERT];
    renderBell();
    const dialog = await openInbox();
    fireEvent.click(within(dialog).getByRole("button", { name: "Cerrar", hidden: true }));
    expect(screen.queryByRole("dialog", { hidden: true })).toBeNull();
  });

  it("sin avisos, la bandeja lo explica", async () => {
    alerts = [];
    renderBell();
    await waitFor(() => expect(bell().getAttribute("aria-label")).toBe("Avisos, ninguno sin leer"));
    fireEvent.click(bell());
    const dialog = await screen.findByRole("dialog", { hidden: true });
    expect(await within(dialog).findByText(/Todavía no hay avisos/)).toBeTruthy();
  });
});
