import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import asset from "../../api/mocks/AssetOut.json";
import transaction from "../../api/mocks/TransactionOut.json";
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
const importada = { ...nueva, id: "personal-2" };

/**
 * `GET /portfolios` devuelve `list`; el resto lo resuelve `handler` (o 404). Como el backend,
 * crear con éxito (201) añade `nueva` a la lista, importar añade `importada` y `DELETE` la quita.
 */
function stubApi(list: { id: string }[], handler: Handler = () => undefined) {
  const fetchMock = vi.fn(async (...[url, init]: FetchArgs) => {
    const method = init?.method ?? "GET";
    if (url === "/api/v1/portfolios" && method === "GET") return json(list);
    const one = /^\/api\/v1\/portfolios\/([^/]+)$/.exec(url);
    if (one && method === "DELETE") {
      const idx = list.findIndex((x) => x.id === one[1]);
      if (idx < 0) return json({ code: "NOT_FOUND" }, 404);
      list.splice(idx, 1);
      return new Response(null, { status: 204 });
    }
    const res = handler(url, init) ?? json({ code: "NOT_FOUND" }, 404);
    if (url === "/api/v1/portfolios" && res.status === 201) list.push(nueva);
    if (url === "/api/v1/portfolios/import" && res.status === 201) list.push(importada);
    return res;
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const createOk: Handler = (url, init) =>
  url === "/api/v1/portfolios" && init?.method === "POST" ? json(nueva, 201) : undefined;

async function goToStep2() {
  await screen.findByRole("heading", { name: "Crea tu primera cartera" });
  fillDetails();
  fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
  const step2 = await screen.findByRole("heading", { name: "Añade los activos de «Personal»" });
  await waitFor(() => expect(document.activeElement).toBe(step2));
}

async function addUnitsOnly(units: string) {
  const input = screen.getByRole("combobox", { name: "Activo" });
  fireEvent.change(input, { target: { value: "IWDA" } });
  const option = await screen.findByRole("option", { name: /iShares Core MSCI World/ });
  fireEvent.keyDown(input, { key: "ArrowDown" });
  await waitFor(() => expect(input.getAttribute("aria-activedescendant")).toBe(option.id));
  fireEvent.keyDown(input, { key: "Enter" });
  fireEvent.change(screen.getByRole("textbox", { name: "Participaciones" }), { target: { value: units } });
  fireEvent.click(screen.getByRole("button", { name: "Guardar posición" }));
}

function chooseCsv(text: string) {
  fireEvent.click(screen.getByRole("button", { name: "Importar un CSV" }));
  const file = new File([text], "cartera.csv", { type: "text/csv" });
  fireEvent.change(screen.getByLabelText("Fichero CSV"), { target: { files: [file] } });
  fireEvent.click(screen.getByRole("button", { name: "Importar" }));
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
    fireEvent.click(await screen.findByRole("button", { name: "Continuar" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Hay 2 campos por revisar");
    expect(screen.getByText("Ponle un nombre a la cartera.")).toBeTruthy();
    expect(screen.getByText("Elige un perfil de riesgo.")).toBeTruthy();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });

  it("el paso 1 solo pide nombre, tipo y perfil; «Continuar» pasa al paso 2", async () => {
    const fetchMock = stubApi([], createOk);
    renderGate();
    await screen.findByRole("heading", { name: "Crea tu primera cartera" });
    expect(screen.queryByRole("radio", { name: /Importar un CSV/ })).toBeNull();
    expect(screen.queryByRole("group", { name: /Cómo quieres añadir/ })).toBeNull();
    await goToStep2();
    expect(screen.getByText("Paso 2 de 2")).toBeTruthy();
    const createCall = fetchMock.mock.calls.find(([u, i]) => u === "/api/v1/portfolios" && i?.method === "POST");
    expect(JSON.parse(String(createCall?.[1]?.body))).toEqual({
      name: "Personal",
      kind: "personal",
      risk_profile: "moderado",
    });
    expect(screen.getByRole("combobox", { name: "Activo" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Importar un CSV" })).toBeTruthy();
  });

  it("a mano: guarda una posición solo con participaciones y luego abre Inicio con ella", async () => {
    const fetchMock = stubApi([], (url, init) => {
      if (url.startsWith("/api/v1/assets/lookup")) return json([asset]);
      if (url === "/api/v1/portfolios/personal-1/transactions") return json(transaction, 201);
      return createOk(url, init);
    });
    renderGate();
    await goToStep2();

    const goHome = screen.getByRole("button", { name: "Ir a Inicio" });
    expect(goHome.getAttribute("aria-disabled")).toBe("true");
    fireEvent.click(goHome);
    expect(screen.queryByTestId("where")).toBeNull();

    await addUnitsOnly("10");
    await waitFor(() => expect(goHome.getAttribute("aria-disabled")).toBe("false"));
    const buy = fetchMock.mock.calls.find(([u]) => u.endsWith("/transactions"));
    expect(JSON.parse(String(buy?.[1]?.body))).toEqual({ type: "buy", asset_id: asset.id, units: "10" });
    // Ya hay una posición guardada a mano: la cartera no se puede sustituir por un CSV.
    expect(screen.queryByRole("button", { name: "Importar un CSV" })).toBeNull();
    fireEvent.click(goHome);
    expect((await screen.findByTestId("where")).textContent).toBe("/inicio?p=personal-1");
  });

  it("con CSV en el paso 2: crea la importada, borra la vacía y abre Inicio con la importada", async () => {
    const line = { asset_id: asset.id, units: "3", avg_cost_eur: "90" };
    const list: { id: string }[] = [];
    const fetchMock = stubApi(list, (url, init) =>
      url === "/api/v1/portfolios/import"
        ? json({ dry_run: false, portfolio: importada, positions: [line] }, 201)
        : createOk(url, init),
    );
    renderGate();
    await goToStep2();
    const toggle = screen.getByRole("button", { name: "Importar un CSV" });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    chooseCsv("asset,units,avg_cost_eur\nIWDA,3,90\n");
    expect(toggle.getAttribute("aria-expanded")).toBe("true");

    const done = await screen.findByText("Hemos importado 1 posición en «Personal».");
    await waitFor(() => expect(document.activeElement).toBe(done.parentElement));
    const call = fetchMock.mock.calls.find(([u]) => u === "/api/v1/portfolios/import");
    expect(JSON.parse(String(call?.[1]?.body))).toEqual({
      name: "Personal",
      kind: "personal",
      risk_profile: "moderado",
      csv: "asset,units,avg_cost_eur\nIWDA,3,90\n",
      dry_run: false,
    });
    const del = fetchMock.mock.calls.find(([, i]) => i?.method === "DELETE");
    expect(del?.[0]).toBe("/api/v1/portfolios/personal-1");
    expect(list.map((p) => p.id)).toEqual(["personal-2"]);

    const goHome = screen.getByRole("button", { name: "Ir a Inicio" });
    expect(goHome.getAttribute("aria-disabled")).toBe("false");
    fireEvent.click(goHome);
    expect((await screen.findByTestId("where")).textContent).toBe("/inicio?p=personal-2");
  });

  it("con CSV con errores: lista cada fila, no borra la vacía y no sale del asistente", async () => {
    const fetchMock = stubApi([], (url, init) =>
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
        : createOk(url, init),
    );
    renderGate();
    await goToStep2();
    chooseCsv("asset,units,avg_cost_eur\nXXX,3,90\n");

    expect(await screen.findByText("Línea 2 (asset): No está en el catálogo.")).toBeTruthy();
    expect(screen.getByText(/No se ha importado ninguna posición/)).toBeTruthy();
    expect(fetchMock.mock.calls.some(([, i]) => i?.method === "DELETE")).toBe(false);
    expect(screen.queryByTestId("where")).toBeNull();
    expect(screen.getByRole("button", { name: "Ir a Inicio" }).getAttribute("aria-disabled")).toBe("true");
  });

  it("CSV vacío: avisa en el campo del fichero sin llamar a la API", async () => {
    const fetchMock = stubApi([], createOk);
    renderGate();
    await goToStep2();
    chooseCsv("  \n");
    expect(await screen.findByText("El fichero está vacío.")).toBeTruthy();
    expect(fetchMock.mock.calls.some(([u]) => u === "/api/v1/portfolios/import")).toBe(false);
  });
});
