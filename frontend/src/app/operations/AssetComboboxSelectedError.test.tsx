import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { AssetOut } from "../../api/generated/schema";
import fund from "../../api/mocks/AssetOut.fund.json";
import { AssetCombobox } from "../onboarding/AssetCombobox";

function renderWith(props: { error?: string; selectedError?: string }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <AssetCombobox label="Fondo de destino" value={fund as AssetOut} onChange={vi.fn()} {...props} />
    </QueryClientProvider>,
  );
}

afterEach(cleanup);

describe("AssetCombobox con activo elegido", () => {
  it("sin selectedError no pinta el error (comportamiento del alta de T1-19)", () => {
    renderWith({ error: "Elige un activo de la lista." });
    expect(screen.queryByText("Elige un activo de la lista.")).toBeNull();
    expect(screen.getByRole("group", { name: "Fondo de destino" }).getAttribute("aria-describedby")).toBeNull();
  });

  it("con selectedError lo pinta y lo enlaza por aria-describedby", () => {
    renderWith({ selectedError: "El destino tiene que ser distinto del origen." });
    const error = screen.getByText("El destino tiene que ser distinto del origen.");
    expect(screen.getByRole("group", { name: "Fondo de destino" }).getAttribute("aria-describedby")).toBe(error.id);
  });
});
