import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import asset from "../../api/mocks/AssetOut.json";
import portfolio from "../../api/mocks/PortfolioOut.json";
import transaction from "../../api/mocks/TransactionOut.json";
import { ApiError } from "../../api/client";
import { OnboardingForm } from "./OnboardingForm";
import { SaveStepError } from "./savePositions";
import { submitErrorText } from "./submitError";
import { emptyLine } from "./positionsDraft";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

type FetchArgs = [string, RequestInit?];

function stubApi({
  positions = () => json(portfolio, 201),
  transactions = () => json(transaction, 201),
}: { positions?: () => Response; transactions?: () => Response } = {}) {
  const fetchMock = vi.fn(async (...[url]: FetchArgs) => {
    if (url.startsWith("/api/v1/assets/lookup")) return json([asset]);
    if (url.endsWith("/transactions")) return transactions();
    return positions();
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderForm() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const invalidate = vi.spyOn(client, "invalidateQueries");
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <OnboardingForm portfolioId="laura" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return { invalidate };
}

async function pickAsset() {
  const input = screen.getByRole("combobox", { name: "Activo" });
  fireEvent.change(input, { target: { value: "IWDA" } });
  const option = await screen.findByRole("option", { name: /iShares Core MSCI World/ });
  fireEvent.keyDown(input, { key: "ArrowDown" });
  await waitFor(() => expect(input.getAttribute("aria-activedescendant")).toBe(option.id));
  fireEvent.keyDown(input, { key: "Enter" });
}

function openPriceAndDate() {
  const toggle = screen.getByRole("button", { name: /Indicar precio de compra y fecha/ });
  expect(toggle.getAttribute("aria-expanded")).toBe("false");
  fireEvent.click(toggle);
  expect(toggle.getAttribute("aria-expanded")).toBe("true");
}

const posts = (fetchMock: ReturnType<typeof stubApi>) =>
  fetchMock.mock.calls.filter(([, init]) => init?.method === "POST");

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("OnboardingForm", () => {
  it("por defecto solo pide activo y participaciones; precio y fecha están plegados", () => {
    stubApi();
    renderForm();
    expect(screen.getByLabelText("Participaciones")).toBeTruthy();
    expect(screen.getByText(/Se registra al precio de hoy/)).toBeTruthy();
    expect(screen.queryByLabelText("Precio medio (€)")).toBeNull();
    expect(screen.queryByLabelText("Fecha de compra")).toBeNull();
    openPriceAndDate();
    expect(screen.getByLabelText("Precio medio (€)")).toBeTruthy();
    expect(screen.getByLabelText("Fecha de compra")).toBeTruthy();
  });

  it("solo con participaciones: compra al precio de hoy con POST /transactions", async () => {
    const fetchMock = stubApi();
    renderForm();
    await pickAsset();
    fireEvent.change(screen.getByLabelText("Participaciones"), { target: { value: "3,5" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar posición" }));

    const result = await screen.findByRole("region", { name: /Posiciones guardadas/ });
    expect(result.getAttribute("data-calc-id")).toBe(transaction.portfolio.calc_id);
    const calls = posts(fetchMock);
    expect(calls.map(([u]) => u)).toEqual(["/api/v1/portfolios/laura/transactions"]);
    expect(JSON.parse(calls[0]![1]?.body as string)).toEqual({
      type: "buy",
      asset_id: "IE00B4L5Y983",
      units: "3.5",
    });
  });

  it("con precio: envía el alta a /positions y muestra valor y asignación del backend", async () => {
    const fetchMock = stubApi();
    renderForm();
    await pickAsset();
    expect(screen.getByRole("group", { name: "Activo" }).textContent).toContain(
      "IE00B4L5Y983 · IWDA · ETF · Renta variable · EUR",
    );
    fireEvent.change(screen.getByLabelText("Participaciones"), { target: { value: "114" } });
    openPriceAndDate();
    fireEvent.change(screen.getByLabelText("Precio medio (€)"), { target: { value: "80,27" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar posición" }));

    const result = await screen.findByRole("region", { name: /Posiciones guardadas/ });
    expect(result.getAttribute("data-calc-id")).toBe(portfolio.calc_id);
    expect(within(result).getByText(/34\.311,68\s€/)).toBeTruthy();
    expect(within(result).getByText(/Renta variable: 72,0\s%/)).toBeTruthy();
    expect(document.activeElement).toBe(result);

    const calls = posts(fetchMock);
    expect(calls.map(([u]) => u)).toEqual(["/api/v1/portfolios/laura/positions"]);
    expect(JSON.parse(calls[0]![1]?.body as string)).toEqual({
      positions: [{ asset_id: "IE00B4L5Y983", units: "114", avg_cost_eur: "80.27" }],
    });
  });

  it("fecha sin precio: error en la fila y no envía nada", async () => {
    const fetchMock = stubApi();
    renderForm();
    await pickAsset();
    fireEvent.change(screen.getByLabelText("Participaciones"), { target: { value: "1" } });
    openPriceAndDate();
    fireEvent.change(screen.getByLabelText("Fecha de compra"), { target: { value: "2024-01-02" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar posición" }));

    expect((await screen.findByRole("alert")).textContent).toContain("Hay 1 campo por revisar.");
    expect(screen.getByText("Para indicar la fecha, indica también el precio de compra.")).toBeTruthy();
    expect(screen.getByLabelText("Fecha de compra").getAttribute("aria-invalid")).toBe("true");
    expect(posts(fetchMock)).toHaveLength(0);
  });

  it("no envía nada si faltan campos: resumen con el foco y error en cada campo", async () => {
    const fetchMock = stubApi();
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: "Guardar posición" }));
    const summary = await screen.findByRole("alert");
    expect(summary.textContent).toContain("Hay 2 campos por revisar.");
    await waitFor(() => expect(document.activeElement).toBe(summary));
    const units = screen.getByLabelText("Participaciones");
    expect(units.getAttribute("aria-invalid")).toBe("true");
    expect(units.getAttribute("aria-describedby")).toMatch(/error/);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("añade y quita filas; el foco va al buscador de la fila nueva", () => {
    stubApi();
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: "Añadir otra posición" }));
    expect(screen.getByRole("group", { name: "Posición 2" })).toBeTruthy();
    const second = within(screen.getByRole("group", { name: "Posición 2" }));
    expect(document.activeElement).toBe(second.getByRole("combobox"));
    expect(screen.getByRole("button", { name: "Guardar 2 posiciones" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Quitar posición 2" }));
    expect(screen.queryByRole("group", { name: "Posición 2" })).toBeNull();
    expect(screen.queryByRole("button", { name: /Quitar/ })).toBeNull();
  });

  it("si el backend rechaza el alta lo explica con el nombre del activo", async () => {
    stubApi({
      positions: () =>
        json({ code: "PRICE_UNAVAILABLE", message: "", details: { asset_id: "IE00B4L5Y983" } }, 503),
    });
    renderForm();
    await pickAsset();
    fireEvent.change(screen.getByLabelText("Participaciones"), { target: { value: "1" } });
    openPriceAndDate();
    fireEvent.change(screen.getByLabelText("Precio medio (€)"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar posición" }));
    expect(
      await screen.findByText(/no hay precio de «iShares Core MSCI World UCITS ETF USD \(Acc\)»/),
    ).toBeTruthy();
  });

  it("si falla la compra sin precio lo explica e invalida las consultas igualmente", async () => {
    stubApi({ transactions: () => json({ code: "PRICE_UNAVAILABLE", message: "", details: {} }, 503) });
    const { invalidate } = renderForm();
    await pickAsset();
    fireEvent.change(screen.getByLabelText("Participaciones"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar posición" }));
    expect(
      await screen.findByText(
        /no hay precio de «iShares Core MSCI World UCITS ETF USD \(Acc\)» para registrarla al precio de hoy\. Indica el precio de compra/,
      ),
    ).toBeTruthy();
    expect(screen.getByText(/No se ha guardado ninguna posición/)).toBeTruthy();
    expect(invalidate).toHaveBeenCalled();
  });
});

describe("submitErrorText", () => {
  it("activo desconocido", () => {
    const err = new ApiError("", 404, "NOT_FOUND", { asset_id: "XX" });
    expect(submitErrorText(err, [emptyLine()])).toBe(
      "No encontramos «XX» en el catálogo. No se ha guardado ninguna posición.",
    );
  });
  it("compra fallida tras otras guardadas: lo dice", () => {
    const err = new SaveStepError("buy", "XX", [1], new ApiError("", 503, "PRICE_UNAVAILABLE"));
    expect(submitErrorText(err, [])).toMatch(/«XX».*Las posiciones anteriores sí se han guardado/);
  });
  it("error genérico", () => {
    expect(submitErrorText(new Error("x"), [])).toMatch(/No hemos podido guardar/);
  });
});
