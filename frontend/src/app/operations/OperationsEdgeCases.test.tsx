import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import fund from "../../api/mocks/AssetOut.fund.json";
import portfolio from "../../api/mocks/PortfolioOut.json";
import txOut from "../../api/mocks/TransactionOut.json";
import transferOut from "../../api/mocks/TransactionOut.transfer.json";
import { ApiError } from "../../api/client";
import type { TransactionOut } from "../../api/generated/schema";
import { OperationsForm } from "./OperationsForm";
import { OperationResult } from "./OperationResult";
import { operationErrorText } from "./operationError";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function stubApi() {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method === "POST") return json(transferOut, 201);
    if (url.startsWith("/api/v1/assets/lookup")) return json([fund]);
    return json(portfolio);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
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

async function pickDestination() {
  const input = screen.getByRole("combobox", { name: "Fondo de destino" });
  fireEvent.change(input, { target: { value: "Vanguard" } });
  const list = await screen.findByRole("listbox", { name: "Activos encontrados" });
  const option = await within(list).findByRole("option", { name: /Vanguard Global Stock/ });
  fireEvent.keyDown(input, { key: "ArrowDown" });
  await waitFor(() => expect(input.getAttribute("aria-activedescendant")).toBe(option.id));
  fireEvent.keyDown(input, { key: "Enter" });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("OperationsForm · casos límite", () => {
  it("al cambiar el origen se borra el error de «destino igual que origen»", async () => {
    stubApi();
    renderForm();
    fireEvent.click(screen.getByRole("radio", { name: "Traspaso" }));
    await screen.findByRole("option", { name: /Apple Inc\./ });
    fireEvent.change(screen.getByLabelText("Fondo de origen"), { target: { value: "IE00B03HD191" } });
    await pickDestination();
    fireEvent.click(screen.getByRole("radio", { name: "Por participaciones" }));
    fireEvent.change(screen.getByLabelText("Participaciones"), { target: { value: "50" } });
    fireEvent.click(screen.getByRole("button", { name: "Registrar traspaso" }));
    await screen.findByText("El destino tiene que ser distinto del origen.");

    fireEvent.change(screen.getByLabelText("Fondo de origen"), { target: { value: "IE00B18GC888" } });
    expect(screen.queryByText("El destino tiene que ser distinto del origen.")).toBeNull();
    const group = screen.getByRole("group", { name: "Fondo de destino" });
    expect(group.getAttribute("aria-describedby")).toBeNull();
  });
});

describe("operationErrorText · precisión", () => {
  it("INSUFFICIENT_UNITS muestra las participaciones disponibles sin redondear a 0", () => {
    const error = new ApiError("x", 422, "INSUFFICIENT_UNITS", { available_units: "0.00004000" });
    expect(operationErrorText(error, "sell", "Apple Inc.")).toContain("en la cartera hay 0,00004.");
  });
});

describe("OperationResult · trazabilidad", () => {
  it("cada cifra mostrada lleva data-calc-id", () => {
    for (const tx of [txOut, transferOut] as TransactionOut[]) {
      const { container, unmount } = render(<OperationResult tx={tx} />);
      const figures = container.querySelectorAll("dd");
      expect(figures.length).toBeGreaterThan(0);
      for (const dd of figures) expect(dd.getAttribute("data-calc-id"), dd.textContent ?? "").toBeTruthy();
      unmount();
    }
  });
});
