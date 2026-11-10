import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import asset from "../../api/mocks/AssetOut.json";
import portfolio from "../../api/mocks/PortfolioOut.json";
import { FirstRunGate } from "./FirstRunGate";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

type FetchArgs = [string, RequestInit?];
type Handler = (url: string, init?: RequestInit) => Response | undefined;

const nueva = { id: "personal-1", name: "Personal", kind: "personal", risk_profile: "moderado", profile: "moderado" };

/**
 * `GET /portfolios` devuelve `list`; el resto lo resuelve `handler` (o 404). Como el backend,
 * una creación o importación con éxito (201) añade `nueva` a la lista.
 */
function stubApi(list: unknown[], handler: Handler = () => undefined) {
  const fetchMock = vi.fn(async (...[url, init]: FetchArgs) => {
    const method = init?.method ?? "GET";
    if (url === "/api/v1/portfolios" && method === "GET") return json(list);
    const res = handler(url, init) ?? json({ code: "NOT_FOUND" }, 404);
    const creates = url === "/api/v1/portfolios" || url === "/api/v1/portfolios/import";
    if (creates && res.status === 201) list.push(nueva);
    return res;
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function Where() {
  const { pathname, search } = useLocation();
  return <p data-testid="where">{`${pathname}${search}`}</p>;
}

function renderGate() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/inicio"]}>
        <Routes>
          <Route
            path="*"
            element={
              <FirstRunGate>
                <nav aria-label="Secciones">app</nav>
                <Where />
              </FirstRunGate>
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function fillDetails(name = "Personal") {
  fireEvent.change(screen.getByRole("textbox", { name: "Nombre de la cartera" }), {
    target: { value: name },
  });
  fireEvent.click(screen.getByRole("radio", { name: /Moderado/ }));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("FirstRunGate", () => {
  it("con carteras, enseña la app", async () => {
    stubApi([nueva]);
    renderGate();
    await waitFor(() => expect(screen.getByTestId("where")).toBeTruthy());
    expect(screen.queryByRole("heading", { name: "Crea tu primera cartera" })).toBeNull();
  });

  it("sin carteras, abre el asistente y no enseña la app", async () => {
    stubApi([]);
    renderGate();
    expect(await screen.findByRole("heading", { name: "Crea tu primera cartera" })).toBeTruthy();
    expect(screen.queryByRole("navigation", { name: "Secciones" })).toBeNull();
    expect(screen.getByText(/usa inteligencia artificial.*No es asesoramiento financiero/)).toBeTruthy();
  });

  it("sin nombre ni perfil, no envía nada y dice qué falta", async () => {
    const fetchMock = stubApi([]);
    renderGate();
    fireEvent.click(await screen.findByRole("button", { name: "Crear la cartera" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Hay 2 campos por revisar");
    expect(screen.getByText("Ponle un nombre a la cartera.")).toBeTruthy();
    expect(screen.getByText("Elige un perfil de riesgo.")).toBeTruthy();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });

  it("a mano: crea la cartera, pide posiciones y luego abre Inicio con ella", async () => {
    const fetchMock = stubApi([], (url, init) => {
      if (url === "/api/v1/portfolios" && init?.method === "POST") return json(nueva, 201);
      if (url.startsWith("/api/v1/assets/lookup")) return json([asset]);
      if (url === "/api/v1/portfolios/personal-1/positions") return json(portfolio, 201);
      return undefined;
    });
    renderGate();
    await screen.findByRole("heading", { name: "Crea tu primera cartera" });
    fillDetails();
    fireEvent.click(screen.getByRole("button", { name: "Crear la cartera" }));

    const step2 = await screen.findByRole("heading", { name: "Añade los activos de «Personal»" });
    await waitFor(() => expect(document.activeElement).toBe(step2));
    const createCall = fetchMock.mock.calls.find(([u, i]) => u === "/api/v1/portfolios" && i?.method === "POST");
    expect(JSON.parse(String(createCall?.[1]?.body))).toEqual({
      name: "Personal",
      kind: "personal",
      risk_profile: "moderado",
    });

    const goHome = screen.getByRole("button", { name: "Ir a Inicio" });
    expect(goHome.getAttribute("aria-disabled")).toBe("true");
    fireEvent.click(goHome);
    expect(screen.queryByTestId("where")).toBeNull();

    const input = screen.getByRole("combobox", { name: "Activo" });
    fireEvent.change(input, { target: { value: "IWDA" } });
    const option = await screen.findByRole("option", { name: /iShares Core MSCI World/ });
    fireEvent.keyDown(input, { key: "ArrowDown" });
    await waitFor(() => expect(input.getAttribute("aria-activedescendant")).toBe(option.id));
    fireEvent.keyDown(input, { key: "Enter" });
    fireEvent.change(screen.getByRole("textbox", { name: "Participaciones" }), { target: { value: "10" } });
    fireEvent.change(screen.getByRole("textbox", { name: /Precio medio/ }), { target: { value: "90" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar posición" }));

    await waitFor(() => expect(goHome.getAttribute("aria-disabled")).toBe("false"));
    fireEvent.click(goHome);
    expect((await screen.findByTestId("where")).textContent).toBe("/inicio?p=personal-1");
  });

  it("con CSV: importa y abre Inicio con la cartera nueva", async () => {
    const fetchMock = stubApi([], (url) =>
      url === "/api/v1/portfolios/import"
        ? json({ dry_run: false, portfolio: nueva, positions: [] }, 201)
        : undefined,
    );
    renderGate();
    await screen.findByRole("heading", { name: "Crea tu primera cartera" });
    fillDetails();
    fireEvent.click(screen.getByRole("radio", { name: /Importar un CSV/ }));
    const file = new File(["asset,units,avg_cost_eur\nIWDA,3,90\n"], "cartera.csv", { type: "text/csv" });
    fireEvent.change(screen.getByLabelText("Fichero CSV"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Importar y crear la cartera" }));

    expect((await screen.findByTestId("where")).textContent).toBe("/inicio?p=personal-1");
    const call = fetchMock.mock.calls.find(([u]) => u === "/api/v1/portfolios/import");
    expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
      name: "Personal",
      csv: "asset,units,avg_cost_eur\nIWDA,3,90\n",
      dry_run: false,
    });
  });

  it("con CSV con errores: lista cada fila y no sale del asistente", async () => {
    stubApi([], (url) =>
      url === "/api/v1/portfolios/import"
        ? json(
            {
              code: "VALIDATION_ERROR",
              details: {
                rows: [{ line: 2, field: "asset", code: "unknown_asset", message: "No está en el catálogo." }],
              },
            },
            422,
          )
        : undefined,
    );
    renderGate();
    await screen.findByRole("heading", { name: "Crea tu primera cartera" });
    fillDetails();
    fireEvent.click(screen.getByRole("radio", { name: /Importar un CSV/ }));
    const file = new File(["asset,units,avg_cost_eur\nXXX,3,90\n"], "cartera.csv");
    fireEvent.change(screen.getByLabelText("Fichero CSV"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Importar y crear la cartera" }));

    expect(await screen.findByText("Línea 2 (asset): No está en el catálogo.")).toBeTruthy();
    expect(screen.getByText(/No se ha creado la cartera/)).toBeTruthy();
    expect(screen.queryByTestId("where")).toBeNull();
  });
});
