import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import portfolio from "../../api/mocks/PortfolioOut.json";
import plan from "../../api/mocks/DcaPlanOut.json";
import execution from "../../api/mocks/DcaExecutionOut.json";
import { DcaSection } from "./DcaSection";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

interface Stub {
  plans?: unknown[];
  pending?: unknown[];
  portfolioStatus?: number;
  write?: () => Response;
}

function stubApi({ plans = [plan], pending = [], portfolioStatus = 200, write }: Stub = {}) {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method === "POST" || init?.method === "PATCH") return write ? write() : json({}, 500);
    if (url.endsWith("/dca-plans")) return json(plans);
    if (url.includes("/dca-executions")) return json(pending);
    return portfolioStatus === 200 ? json(portfolio) : json({ code: "UPSTREAM_UNAVAILABLE" }, portfolioStatus);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
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

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const ALREADY = "ya estaba confirmada o saltada";

describe("aportaciones pendientes · casos límite", () => {
  it("un 422 que no es «ya resuelta» se muestra como error en la tarjeta", async () => {
    stubApi({
      pending: [execution],
      write: () => json({ code: "VALIDATION_ERROR", message: "Cuerpo no válido.", details: {} }, 422),
    });
    renderSection();
    fireEvent.click(await screen.findByRole("button", { name: "Confirmar aportación" }));
    expect(await screen.findByText(/No hemos podido guardar la respuesta/)).toBeTruthy();
    expect(screen.queryByText(new RegExp(ALREADY))).toBeNull();
  });

  it("el 422 de «ya resuelta» (con execution_id y status) se reconoce", async () => {
    stubApi({
      pending: [execution],
      write: () =>
        json(
          {
            code: "VALIDATION_ERROR",
            message: "Esta aportación ya está confirmada.",
            details: { execution_id: execution.id, status: "confirmed" },
          },
          422,
        ),
    });
    renderSection();
    fireEvent.click(await screen.findByRole("button", { name: "Confirmar aportación" }));
    expect(await screen.findByText(new RegExp(ALREADY))).toBeTruthy();
  });

  it("tras confirmar, los botones siguen desactivados hasta que la tarjeta desaparece", async () => {
    // La lista pendiente no cambia en este stub: la tarjeta sigue ahí tras recargar.
    const fetchMock = stubApi({ pending: [execution], write: () => json({ ...execution, status: "confirmed" }) });
    renderSection();
    fireEvent.click(await screen.findByRole("button", { name: "Confirmar aportación" }));
    await screen.findByText(/confirmada y registrada en la cartera/);
    const confirm = screen.getByRole("button", { name: "Confirmar aportación" }) as HTMLButtonElement;
    const skip = screen.getByRole("button", { name: "Saltar esta vez" }) as HTMLButtonElement;
    expect(confirm.disabled).toBe(true);
    expect(skip.disabled).toBe(true);
    fireEvent.click(confirm);
    expect(fetchMock.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
  });
});

describe("planes · casos límite", () => {
  it("«Editar plan» no se abre sin la cartera cargada (no hay nombres de activos)", async () => {
    stubApi({ portfolioStatus: 503 });
    renderSection();
    const edit = (await screen.findByRole("button", { name: "Editar plan" })) as HTMLButtonElement;
    await waitFor(() => expect(edit.disabled).toBe(true));
  });

  it("los pesos del plan se ven con toda su precisión", async () => {
    const thirds = {
      ...plan,
      allocations: [
        { asset_id: "IE00B03HD191", weight: "0.33333333" },
        { asset_id: "IE00B18GC888", weight: "0.33333333" },
        { asset_id: "IE00B4L5Y983", weight: "0.33333334" },
      ],
    };
    stubApi({ plans: [thirds] });
    renderSection();
    const list = await screen.findByRole("list", { name: "Reparto" });
    expect(list.textContent).toMatch(/33,333333\s%/);
    expect(list.textContent).toMatch(/33,333334\s%/);
  });

  it("un peso redondo se sigue viendo corto", async () => {
    stubApi();
    renderSection();
    const list = await screen.findByRole("list", { name: "Reparto" });
    expect(list.textContent).toMatch(/70\s%/);
    expect(list.textContent).not.toMatch(/70,0/);
  });
});
