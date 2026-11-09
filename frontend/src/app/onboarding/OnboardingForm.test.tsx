import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import asset from "../../api/mocks/AssetOut.json";
import portfolio from "../../api/mocks/PortfolioOut.json";
import { ApiError } from "../../api/client";
import { OnboardingForm } from "./OnboardingForm";
import { submitErrorText } from "./submitError";
import { emptyLine } from "./positionsDraft";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

type FetchArgs = [string, RequestInit?];

function stubApi(positions: () => Response = () => json(portfolio, 201)) {
  const fetchMock = vi.fn(async (...[url]: FetchArgs) =>
    url.startsWith("/api/v1/assets/lookup") ? json([asset]) : positions(),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderForm() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <OnboardingForm portfolioId="laura" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function pickAsset() {
  const input = screen.getByRole("combobox", { name: "Activo" });
  fireEvent.change(input, { target: { value: "IWDA" } });
  const option = await screen.findByRole("option", { name: /iShares Core MSCI World/ });
  fireEvent.keyDown(input, { key: "ArrowDown" });
  await waitFor(() => expect(input.getAttribute("aria-activedescendant")).toBe(option.id));
  fireEvent.keyDown(input, { key: "Enter" });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("OnboardingForm", () => {
  it("busca el activo, envía el alta y muestra valor y asignación del backend", async () => {
    const fetchMock = stubApi();
    renderForm();
    await pickAsset();
    expect(screen.getByRole("group", { name: "Activo" }).textContent).toContain(
      "IE00B4L5Y983 · IWDA · ETF · Renta variable · EUR",
    );
    fireEvent.change(screen.getByLabelText("Participaciones"), { target: { value: "114" } });
    fireEvent.change(screen.getByLabelText("Precio medio (€)"), { target: { value: "80,27" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar posición" }));

    const result = await screen.findByRole("region", { name: /Posiciones guardadas/ });
    expect(result.getAttribute("data-calc-id")).toBe(portfolio.calc_id);
    expect(within(result).getByText(/34\.311,68\s€/)).toBeTruthy();
    expect(within(result).getByText(/Renta variable: 72,0\s%/)).toBeTruthy();
    expect(document.activeElement).toBe(result);

    const post = fetchMock.mock.calls.find(([url]) => url.endsWith("/positions"))!;
    expect(post[0]).toBe("/api/v1/portfolios/laura/positions");
    expect(JSON.parse(post[1]?.body as string)).toEqual({
      positions: [{ asset_id: "IE00B4L5Y983", units: "114", avg_cost_eur: "80.27" }],
    });
  });

  it("no envía nada si faltan campos: resumen con el foco y error en cada campo", async () => {
    const fetchMock = stubApi();
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: "Guardar posición" }));
    const summary = await screen.findByRole("alert");
    expect(summary.textContent).toContain("Hay 3 campos por revisar.");
    await waitFor(() => expect(document.activeElement).toBe(summary));
    const units = screen.getByLabelText("Participaciones");
    expect(units.getAttribute("aria-invalid")).toBe("true");
    expect(units.getAttribute("aria-describedby")).toMatch(/error/);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("añade y quita filas; el foco va al buscador de la fila nueva", async () => {
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
    stubApi(() =>
      json({ code: "PRICE_UNAVAILABLE", message: "", details: { asset_id: "IE00B4L5Y983" } }, 503),
    );
    renderForm();
    await pickAsset();
    fireEvent.change(screen.getByLabelText("Participaciones"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Precio medio (€)"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar posición" }));
    expect(
      await screen.findByText(/no hay precio de «iShares Core MSCI World UCITS ETF USD \(Acc\)»/),
    ).toBeTruthy();
  });
});

describe("submitErrorText", () => {
  it("activo desconocido", () => {
    const err = new ApiError("", 404, "NOT_FOUND", { asset_id: "XX" });
    expect(submitErrorText(err, [emptyLine()])).toBe(
      "No encontramos «XX» en el catálogo. No se ha guardado ninguna posición.",
    );
  });
  it("error genérico", () => {
    expect(submitErrorText(new Error("x"), [])).toMatch(/No hemos podido guardar/);
  });
});
