import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import type { AlertOut } from "../../api/generated/schema";
import alertMock from "../../api/mocks/AlertOut.json";
import { TraceProvider } from "../../components/trace/TraceProvider";
import { AlertsBell } from "./AlertsBell";
import { inboxPortfolios, mergeAlerts } from "./useAllAlerts";

/** Bandeja con varias carteras (T4-15): los avisos de todas, con su cartera y filtro. */

const PORTFOLIOS = [
  { id: "laura", name: "Laura", profile: "moderado" },
  { id: "javier", name: "Javier", profile: "moderado" },
  { id: "pf_hijos", name: "Hijos", profile: "conservador", kind: "family" },
];

function alert(id: string, createdAt: string, message: string): AlertOut {
  return { ...(alertMock as AlertOut), id, event_id: null, created_at: createdAt, message };
}

const ALERTS: Record<string, AlertOut[]> = {
  laura: [alert("alr_laura", "2026-11-08T18:00:00Z", "Aviso de Laura.")],
  javier: [],
  pf_hijos: [alert("alr_hijos", "2026-11-09T09:00:00Z", "Aviso de Hijos.")],
};

const fetchMock = vi.fn((input: RequestInfo | URL) => {
  const url = String(input);
  const match = /\/portfolios\/([^/]+)\/alerts/.exec(url);
  const body = match
    ? (ALERTS[decodeURIComponent(match[1]!)] ?? [])
    : /\/portfolios(\?|$)/.test(url)
      ? PORTFOLIOS
      : [];
  return Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));
});

function renderBell() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/inicio?p=laura"]}>
        <TraceProvider>
          <AlertsBell />
        </TraceProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const bell = () => screen.getByRole("button", { name: /^Avisos/ });

async function openInbox() {
  await waitFor(() => expect(bell().getAttribute("aria-label")).toBe("Avisos, 2 sin leer"));
  fireEvent.click(bell());
  return screen.findByRole("dialog", { name: "Avisos", hidden: true });
}

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal("fetch", fetchMock);
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

describe("Avisos con varias carteras", () => {
  it("la campana cuenta los no leídos de todas las carteras", async () => {
    renderBell();
    await waitFor(() => expect(bell().getAttribute("aria-label")).toBe("Avisos, 2 sin leer"));
  });

  it("junta los avisos, del más reciente al más antiguo, cada uno con su cartera", async () => {
    renderBell();
    const dialog = await openInbox();
    const items = within(dialog).getAllByRole("article", { hidden: true });
    expect(items.map((i) => within(i).getByText(/^Aviso de/).textContent)).toEqual([
      "Aviso de Hijos.",
      "Aviso de Laura.",
    ]);
    expect(within(items[0]!).getByText("Cartera «Hijos»")).toBeTruthy();
    expect(within(items[1]!).getByText("Cartera «Laura»")).toBeTruthy();
  });

  it("filtra por cartera y explica cuando una no tiene avisos", async () => {
    renderBell();
    const dialog = await openInbox();
    const select = within(dialog).getByLabelText("Cartera");
    fireEvent.change(select, { target: { value: "pf_hijos" } });
    expect(within(dialog).getAllByRole("article", { hidden: true })).toHaveLength(1);
    fireEvent.change(select, { target: { value: "javier" } });
    expect(within(dialog).queryAllByRole("article", { hidden: true })).toHaveLength(0);
    expect(within(dialog).getByText(/no hay avisos de la cartera «Javier»/)).toBeTruthy();
  });

  it("«Marcar todos como leídos» con filtro solo marca los de esa cartera, en su cartera", async () => {
    renderBell();
    const dialog = await openInbox();
    fireEvent.change(within(dialog).getByLabelText("Cartera"), { target: { value: "pf_hijos" } });
    fireEvent.click(
      within(dialog).getByRole("button", { name: "Marcar todos como leídos", hidden: true }),
    );
    expect(bell().getAttribute("aria-label")).toBe("Avisos, 1 sin leer");
    expect(localStorage.getItem("kairos-alerts-read:pf_hijos")).toContain("alr_hijos");
    expect(localStorage.getItem("kairos-alerts-read:laura")).toBeNull();
  });
});

describe("inboxPortfolios y mergeAlerts", () => {
  it("siempre incluye la cartera elegida y descarta entradas sin id", () => {
    expect(inboxPortfolios(undefined, "laura")).toEqual([{ id: "laura", name: "laura" }]);
    expect(inboxPortfolios([{}], "laura")).toEqual([{ id: "laura", name: "laura" }]);
    expect(inboxPortfolios([{ id: "javier", name: "Javier" }], "laura").map((p) => p.id)).toEqual([
      "laura",
      "javier",
    ]);
  });

  it("ordena por fecha y desempata por id", () => {
    const a = alert("b", "2026-11-08T10:00:00Z", "");
    const b = alert("a", "2026-11-08T10:00:00Z", "");
    const c = alert("c", "2026-11-09T10:00:00Z", "");
    const merged = mergeAlerts(
      [
        { id: "x", name: "X" },
        { id: "y", name: "Y" },
      ],
      [[a], [b, c]],
    );
    expect(merged.map((m) => m.alert.id)).toEqual(["c", "a", "b"]);
  });
});
