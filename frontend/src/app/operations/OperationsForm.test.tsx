import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import etf from "../../api/mocks/AssetOut.json";
import fund from "../../api/mocks/AssetOut.fund.json";
import portfolio from "../../api/mocks/PortfolioOut.json";
import txOut from "../../api/mocks/TransactionOut.json";
import transferOut from "../../api/mocks/TransactionOut.transfer.json";
import notAllowed from "../../api/mocks/ErrorOut.transfer_not_allowed.json";
import { ApiError } from "../../api/client";
import { OperationsForm } from "./OperationsForm";
import { operationErrorText } from "./operationError";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

type FetchArgs = [string, RequestInit?];

/** GET de cartera y catálogo reales del mock; el POST responde lo que diga cada test. */
function stubApi(write: () => Response) {
  const fetchMock = vi.fn(async (...[url, init]: FetchArgs) => {
    if (init?.method === "POST") return write();
    if (url.startsWith("/api/v1/assets/lookup")) return json(url.includes("IWDA") ? [etf] : [fund]);
    return json(portfolio);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function posted(fetchMock: ReturnType<typeof stubApi>): { url: string; body: unknown } {
  const call = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
  if (!call) throw new Error("no hubo POST");
  return { url: call[0], body: JSON.parse(String(call[1]?.body)) };
}

function renderForm() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <OperationsForm portfolioId="laura" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function pickAsset(label: string, query: string, name: RegExp) {
  const input = screen.getByRole("combobox", { name: label });
  fireEvent.change(input, { target: { value: query } });
  // Solo en la lista del buscador: el desplegable de posiciones también tiene opciones.
  const list = await screen.findByRole("listbox", { name: "Activos encontrados" });
  const option = await within(list).findByRole("option", { name });
  fireEvent.keyDown(input, { key: "ArrowDown" });
  await waitFor(() => expect(input.getAttribute("aria-activedescendant")).toBe(option.id));
  fireEvent.keyDown(input, { key: "Enter" });
}

async function choosePosition(label: string, assetId: string) {
  await screen.findByRole("option", { name: /Apple Inc\./ });
  fireEvent.change(screen.getByLabelText(label), { target: { value: assetId } });
}

const typeQty = (label: string, value: string) =>
  fireEvent.change(screen.getByLabelText(label), { target: { value } });

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("OperationsForm · compra", () => {
  it("por importe envía amount_eur y muestra lo que devuelve el backend", async () => {
    const fetchMock = stubApi(() => json({ ...txOut, type: "buy", asset_id: etf.id }, 201));
    renderForm();
    await pickAsset("Activo", "IWDA", /iShares Core MSCI World/);
    typeQty("Importe (€)", "300,5");
    fireEvent.click(screen.getByRole("button", { name: "Registrar compra" }));

    const result = await screen.findByRole("region", { name: "Compra registrada" });
    const { url, body } = posted(fetchMock);
    expect(url).toBe("/api/v1/portfolios/laura/transactions");
    expect(body).toEqual({ type: "buy", asset_id: "IE00B4L5Y983", amount_eur: "300.5" });
    expect(result.getAttribute("data-calc-id")).toBe(txOut.calc_id);
    expect(result.textContent).toMatch(/393,29/);
  });

  it("por participaciones envía units", async () => {
    const fetchMock = stubApi(() => json({ ...txOut, type: "buy" }, 201));
    renderForm();
    await pickAsset("Activo", "IWDA", /iShares Core MSCI World/);
    fireEvent.click(screen.getByRole("radio", { name: "Por participaciones" }));
    typeQty("Participaciones", "2,5");
    fireEvent.click(screen.getByRole("button", { name: "Registrar compra" }));
    await screen.findByRole("region", { name: "Compra registrada" });
    expect(posted(fetchMock).body).toEqual({ type: "buy", asset_id: "IE00B4L5Y983", units: "2.5" });
  });

  it("sin activo ni cantidad no llama a la API y marca los campos", async () => {
    const fetchMock = stubApi(() => json(txOut, 201));
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: "Registrar compra" }));
    expect(await screen.findByText("Elige el activo.")).toBeTruthy();
    expect(screen.getByLabelText("Importe (€)").getAttribute("aria-invalid")).toBe("true");
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });
});

describe("OperationsForm · venta", () => {
  it("muestra la plusvalía estimada con su calc_id", async () => {
    const fetchMock = stubApi(() => json(txOut, 201));
    renderForm();
    fireEvent.click(screen.getByRole("radio", { name: "Venta" }));
    await choosePosition("Posición", "US0378331005");
    typeQty("Participaciones", "2");
    fireEvent.click(screen.getByRole("button", { name: "Registrar venta" }));

    const result = await screen.findByRole("region", { name: "Venta registrada" });
    expect(posted(fetchMock).body).toEqual({ type: "sell", asset_id: "US0378331005", units: "2" });
    const gain = screen.getByText(/41,21/);
    expect(gain.getAttribute("data-calc-id")).toBe(txOut.calc_id);
    expect(result.textContent).toContain("Plusvalía estimada");
  });

  it("con INSUFFICIENT_UNITS explica cuántas hay y que no se registró nada", async () => {
    stubApi(() =>
      json(
        {
          code: "INSUFFICIENT_UNITS",
          message: "Solo tienes 4 participaciones de este activo.",
          details: { asset_id: "US0378331005", requested_units: "10", available_units: "4.00000000" },
        },
        422,
      ),
    );
    renderForm();
    fireEvent.click(screen.getByRole("radio", { name: "Venta" }));
    await choosePosition("Posición", "US0378331005");
    typeQty("Participaciones", "10");
    fireEvent.click(screen.getByRole("button", { name: "Registrar venta" }));
    expect(
      await screen.findByText(
        "No hay tantas participaciones de «Apple Inc.»: en la cartera hay 4. No se ha registrado nada.",
      ),
    ).toBeTruthy();
    expect(screen.queryByRole("region", { name: "Venta registrada" })).toBeNull();
  });
});

describe("OperationsForm · traspaso", () => {
  async function fillTransfer(fromId: string, byAmount = false) {
    fireEvent.click(screen.getByRole("radio", { name: "Traspaso" }));
    await choosePosition("Fondo de origen", fromId);
    await pickAsset("Fondo de destino", "Vanguard", /Vanguard Global Stock/);
    if (byAmount) {
      fireEvent.click(screen.getByRole("radio", { name: "Por importe (€)" }));
      typeQty("Importe (€)", "1234,5");
    } else {
      fireEvent.click(screen.getByRole("radio", { name: "Por participaciones" }));
      typeQty("Participaciones", "50");
    }
    fireEvent.click(screen.getByRole("button", { name: "Registrar traspaso" }));
  }

  it("fondo → fondo llama a /transfers y dice que conserva coste y fecha", async () => {
    const fetchMock = stubApi(() => json(transferOut, 201));
    renderForm();
    await fillTransfer("IE00B18GC888");
    const result = await screen.findByRole("region", { name: "Traspaso registrado" });
    const { url, body } = posted(fetchMock);
    expect(url).toBe("/api/v1/portfolios/laura/transfers");
    expect(body).toEqual({ from_asset_id: "IE00B18GC888", to_asset_id: "IE00B03HD191", units: "50" });
    expect(result.textContent).toContain("Se conservan el coste y la fecha de compra");
  });

  it("ETF → TRANSFER_NOT_ALLOWED explica la alternativa con la plusvalía estimada", async () => {
    stubApi(() =>
      json({ ...notAllowed, details: { ...notAllowed.details, calc_id: "calc_gain" } }, 422),
    );
    renderForm();
    await fillTransfer("IE00B4L5Y983");
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Solo los traspasos entre fondos de inversión aplazan los impuestos");
    expect(alert.textContent).toContain("el origen es un ETF");
    expect(alert.textContent).toContain("registrar una venta del origen y después una compra del destino");
    expect(alert.textContent).toMatch(/plusvalía estimada de esas participaciones es de 1105,50/);
    expect(screen.getByText(/1105,50/).getAttribute("data-calc-id")).toBe("calc_gain");
    expect(alert.textContent).not.toMatch(/te recomiendo|deberías/i);
    await waitFor(() => expect(document.activeElement).toBe(alert));
  });

  it("sin plusvalía estimable (null) lo dice sin inventar cifras", async () => {
    stubApi(() =>
      json(
        { ...notAllowed, details: { ...notAllowed.details, estimated_gain_eur: null, calc_id: null } },
        422,
      ),
    );
    renderForm();
    await fillTransfer("IE00B4L5Y983");
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("ahora mismo no podemos estimar su plusvalía");
    expect(alert.textContent).not.toMatch(/\d+,\d{2}\s*€/);
  });

  it("«Registrar como venta» pasa a venta con el origen y la cantidad", async () => {
    stubApi(() => json(notAllowed, 422));
    renderForm();
    await fillTransfer("IE00B4L5Y983");
    fireEvent.click(await screen.findByRole("button", { name: "Registrar como venta" }));
    expect((screen.getByRole("radio", { name: "Venta" }) as HTMLInputElement).checked).toBe(true);
    expect((screen.getByLabelText("Posición") as HTMLSelectElement).value).toBe("IE00B4L5Y983");
    expect((screen.getByLabelText("Participaciones") as HTMLInputElement).value).toBe("50");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("origen y destino iguales: error en el campo, sin llamar a la API", async () => {
    const fetchMock = stubApi(() => json(transferOut, 201));
    renderForm();
    await fillTransfer("IE00B03HD191");
    const error = await screen.findByText("El destino tiene que ser distinto del origen.");
    const group = screen.getByRole("group", { name: "Fondo de destino" });
    expect(group.getAttribute("aria-describedby")).toBe(error.id);
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });

  it("«Registrar como venta» toma importe y unidad del traspaso enviado", async () => {
    stubApi(() => json(notAllowed, 422));
    renderForm();
    await fillTransfer("IE00B4L5Y983", true);
    const sellButton = await screen.findByRole("button", { name: "Registrar como venta" });
    // El borrador cambia después del 422: la venta debe salir de lo que se envió.
    fireEvent.click(screen.getByRole("radio", { name: "Por participaciones" }));
    typeQty("Participaciones", "7");
    fireEvent.click(sellButton);
    expect((screen.getByRole("radio", { name: "Por importe (€)" }) as HTMLInputElement).checked).toBe(true);
    expect((screen.getByLabelText("Importe (€)") as HTMLInputElement).value).toBe("1234,5");
  });

  it("si la posición de origen desaparece, el resultado usa el nombre conocido al enviar", async () => {
    const emptied = {
      ...transferOut,
      asset_id: "IE00B18GC888",
      to_asset_id: "IE00B03HD191",
      portfolio: {
        ...transferOut.portfolio,
        positions: transferOut.portfolio.positions.filter((p) => p.asset_id !== "IE00B18GC888"),
      },
    };
    stubApi(() => json(emptied, 201));
    renderForm();
    await fillTransfer("IE00B18GC888");
    const result = await screen.findByRole("region", { name: "Traspaso registrado" });
    expect(result.textContent).toContain("De «Vanguard Global Bond Index Fund EUR Hedged Acc»");
    expect(result.textContent).not.toContain("«IE00B18GC888»");
  });
});

describe("OperationsForm · otros errores y cambios de tipo", () => {
  it("cambiar de tipo vacía la cantidad para no cambiarle la unidad", async () => {
    const fetchMock = stubApi(() => json(txOut, 201));
    renderForm();
    typeQty("Importe (€)", "500");
    fireEvent.click(screen.getByRole("radio", { name: "Venta" }));
    await choosePosition("Posición", "US0378331005");
    expect((screen.getByLabelText("Participaciones") as HTMLInputElement).value).toBe("");
    fireEvent.click(screen.getByRole("button", { name: "Registrar venta" }));
    expect(await screen.findByText("Escribe una cifra.")).toBeTruthy();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });

  it("503 PRICE_UNAVAILABLE: sin precio no se registra nada", async () => {
    stubApi(() => json({ code: "PRICE_UNAVAILABLE", message: "x", details: { asset_id: etf.id } }, 503));
    renderForm();
    await pickAsset("Activo", "IWDA", /iShares Core MSCI World/);
    typeQty("Importe (€)", "300");
    fireEvent.click(screen.getByRole("button", { name: "Registrar compra" }));
    expect(
      await screen.findByText(
        "Ahora mismo no hay precio de «iShares Core MSCI World UCITS ETF USD (Acc)» para registrar la operación. No se ha registrado nada.",
      ),
    ).toBeTruthy();
  });
});

describe("operationErrorText · 404", () => {
  const notFound = (details: Record<string, unknown>) => new ApiError("x", 404, "NOT_FOUND", details);
  it("distingue activo, cartera y caso sin detalles", () => {
    expect(operationErrorText(notFound({ asset_id: "X" }), "buy", null)).toMatch(/^No encontramos ese activo/);
    expect(operationErrorText(notFound({ portfolio_id: "laura" }), "buy", null)).toMatch(/^No encontramos esta cartera/);
    expect(operationErrorText(notFound({}), "sell", null)).toMatch(/^No encontramos lo necesario/);
  });
});
