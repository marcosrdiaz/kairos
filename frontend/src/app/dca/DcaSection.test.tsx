import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import etf from "../../api/mocks/AssetOut.json";
import fund from "../../api/mocks/AssetOut.fund.json";
import portfolio from "../../api/mocks/PortfolioOut.json";
import plan from "../../api/mocks/DcaPlanOut.json";
import execution from "../../api/mocks/DcaExecutionOut.json";
import { DcaSection } from "./DcaSection";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

type FetchArgs = [string, RequestInit?];

interface Stub {
  plans?: unknown[];
  pending?: unknown[];
  write?: (url: string, init: RequestInit) => Response;
}

function stubApi({ plans = [plan], pending = [], write }: Stub = {}) {
  const fetchMock = vi.fn(async (...[url, init]: FetchArgs) => {
    if (init?.method === "POST" || init?.method === "PATCH") {
      return write ? write(url, init) : json({}, 500);
    }
    if (url.startsWith("/api/v1/assets/lookup")) return json(url.includes("IWDA") ? [etf] : [fund]);
    if (url.endsWith("/dca-plans")) return json(plans);
    if (url.includes("/dca-executions")) return json(pending);
    return json(portfolio);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function writes(fetchMock: ReturnType<typeof stubApi>) {
  return fetchMock.mock.calls
    .filter(([, init]) => init?.method === "POST" || init?.method === "PATCH")
    .map(([url, init]) => ({ url, method: init?.method, body: JSON.parse(String(init?.body)) }));
}

function renderSection() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/cartera?p=laura"]}>
        <DcaSection />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function pickAsset(label: string, query: string, name: RegExp) {
  const input = screen.getByRole("combobox", { name: label });
  fireEvent.change(input, { target: { value: query } });
  const option = await screen.findByRole("option", { name });
  fireEvent.keyDown(input, { key: "ArrowDown" });
  await waitFor(() => expect(input.getAttribute("aria-activedescendant")).toBe(option.id));
  fireEvent.keyDown(input, { key: "Enter" });
}

const type = (label: string, value: string) =>
  fireEvent.change(screen.getByLabelText(label), { target: { value } });

async function fillNewPlan(first: string, second: string) {
  fireEvent.click(await screen.findByRole("button", { name: "Crear un plan de aportaciones" }));
  type("Importe de cada aportación (€)", "300");
  await pickAsset("Activo 1", "Vanguard", /Vanguard Global Stock/);
  type("Porcentaje del activo 1 (%)", first);
  fireEvent.click(screen.getByRole("button", { name: "Añadir otro activo" }));
  await pickAsset("Activo 2", "IWDA", /iShares Core MSCI World/);
  type("Porcentaje del activo 2 (%)", second);
  fireEvent.click(screen.getByRole("button", { name: "Crear plan" }));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("DcaSection · planes", () => {
  it("muestra el plan con nombres de la cartera, reparto y próxima aportación", async () => {
    stubApi();
    renderSection();
    const card = await screen.findByRole("article", { name: /Plan de 300,00/ });
    expect(card.textContent).toContain("cada mes, el día 5");
    expect(card.textContent).toContain("Activo");
    await within(card).findByText("Vanguard Global Stock Index Fund EUR Acc");
    expect(card.textContent).toMatch(/70,0\s*%/);
    expect(card.textContent).toContain("Próxima aportación: 5 de noviembre de 2026");
  });

  it("sin planes muestra el estado vacío", async () => {
    stubApi({ plans: [] });
    renderSection();
    expect(await screen.findByText("Esta cartera aún no tiene ningún plan de aportaciones.")).toBeTruthy();
  });

  it("pausar envía PATCH con status paused", async () => {
    const fetchMock = stubApi({ write: () => json({ ...plan, status: "paused" }) });
    renderSection();
    fireEvent.click(await screen.findByRole("button", { name: "Pausar plan" }));
    await waitFor(() => expect(writes(fetchMock)).toHaveLength(1));
    expect(writes(fetchMock)[0]).toEqual({
      url: "/api/v1/portfolios/laura/dca-plans/dca_laura",
      method: "PATCH",
      body: { status: "paused" },
    });
  });

  it("editar precarga el plan y envía los cambios por PATCH", async () => {
    const fetchMock = stubApi({ write: () => json({ ...plan, amount_eur: "400.00" }) });
    renderSection();
    await screen.findByText("Vanguard Global Stock Index Fund EUR Acc");
    fireEvent.click(screen.getByRole("button", { name: "Editar plan" }));
    const amount = screen.getByLabelText("Importe de cada aportación (€)") as HTMLInputElement;
    expect(amount.value).toBe("300,00");
    expect((screen.getByLabelText("Porcentaje del activo 1 (%)") as HTMLInputElement).value).toBe("70");
    expect((screen.getByLabelText("Porcentaje del activo 2 (%)") as HTMLInputElement).value).toBe("30");
    type("Importe de cada aportación (€)", "400");
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await waitFor(() => expect(writes(fetchMock)).toHaveLength(1));
    expect(writes(fetchMock)[0]?.body).toEqual({
      amount_eur: "400",
      frequency: "monthly",
      day: 5,
      allocations: [
        { asset_id: "IE00B03HD191", weight: "0.7" },
        { asset_id: "IE00B18GC888", weight: "0.3" },
      ],
    });
  });

  it("si el reparto no suma 100 % lo dice y no llama a la API", async () => {
    const fetchMock = stubApi({ plans: [] });
    renderSection();
    await fillNewPlan("70", "20");
    expect(await screen.findByText("El reparto suma 90 % y tiene que sumar 100 %.")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toContain("Hay 1 dato por revisar.");
    expect(writes(fetchMock)).toHaveLength(0);
  });

  it("crea el plan con pesos como fracción", async () => {
    const fetchMock = stubApi({ plans: [], write: () => json(plan, 201) });
    renderSection();
    await fillNewPlan("70", "30");
    expect(await screen.findByText("Plan de aportaciones creado.")).toBeTruthy();
    expect(writes(fetchMock)[0]).toEqual({
      url: "/api/v1/portfolios/laura/dca-plans",
      method: "POST",
      body: {
        amount_eur: "300",
        frequency: "monthly",
        day: 1,
        status: "active",
        allocations: [
          { asset_id: "IE00B03HD191", weight: "0.7" },
          { asset_id: "IE00B4L5Y983", weight: "0.3" },
        ],
      },
    });
  });

  it("un 422 DCA_ALLOCATION_INVALID del backend se explica", async () => {
    stubApi({
      plans: [],
      write: () => json({ code: "DCA_ALLOCATION_INVALID", message: "x", details: { reason: "y" } }, 422),
    });
    renderSection();
    await fillNewPlan("70", "30");
    expect(await screen.findByText(/El reparto no es válido: tiene que sumar 100 %/)).toBeTruthy();
  });
});

describe("DcaSection · aportaciones pendientes", () => {
  it("muestra importe, participaciones estimadas y aviso de precio del momento", async () => {
    stubApi({ pending: [execution] });
    renderSection();
    const item = await screen.findByRole("heading", { name: "Aportación del 5 de noviembre de 2026" });
    const card = item.closest("li")!;
    expect(card.textContent).toMatch(/210,00/);
    expect(card.textContent).toMatch(/unas 4,3568 participaciones/);
    expect(card.textContent).toContain("las participaciones pueden variar");
  });

  it("confirmar envía action confirm y lo anuncia", async () => {
    const fetchMock = stubApi({
      pending: [execution],
      write: () => json({ ...execution, status: "confirmed" }),
    });
    renderSection();
    fireEvent.click(await screen.findByRole("button", { name: "Confirmar aportación" }));
    expect(await screen.findByText(/confirmada y registrada en la cartera/)).toBeTruthy();
    expect(writes(fetchMock)[0]).toEqual({
      url: "/api/v1/dca-executions/dcx_7f3a21",
      method: "POST",
      body: { action: "confirm" },
    });
  });

  it("saltar envía action skip y lo anuncia", async () => {
    const fetchMock = stubApi({
      pending: [execution],
      write: () => json({ ...execution, status: "skipped" }),
    });
    renderSection();
    fireEvent.click(await screen.findByRole("button", { name: "Saltar esta vez" }));
    expect(await screen.findByText(/saltada\. El plan sigue igual\./)).toBeTruthy();
    expect(writes(fetchMock)[0]?.body).toEqual({ action: "skip" });
  });

  it("si ya estaba resuelta (422) lo dice", async () => {
    stubApi({
      pending: [execution],
      write: () => json({ code: "VALIDATION_ERROR", message: "Esta aportación ya está confirmada." }, 422),
    });
    renderSection();
    fireEvent.click(await screen.findByRole("button", { name: "Confirmar aportación" }));
    expect(await screen.findByText("Esta aportación ya estaba confirmada o saltada.")).toBeTruthy();
  });
});
