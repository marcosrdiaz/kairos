import { afterEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import asset from "../../api/mocks/AssetOut.json";
import type { AssetOut } from "../../api/generated/schema";
import { AssetCombobox } from "./AssetCombobox";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

type FetchArgs = [string, RequestInit?];

/** `lookup`: resultados locales; `create`: respuesta de `POST /assets`. */
function stubApi(lookup: unknown[], create: () => Response | Promise<Response> = () => json(asset, 201)) {
  const fetchMock = vi.fn(async (...[url]: FetchArgs) =>
    url.startsWith("/api/v1/assets/lookup") ? json(lookup) : create(),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function Harness({ allowMarketSearch }: { allowMarketSearch: boolean }) {
  const [value, setValue] = useState<AssetOut | null>(null);
  return (
    <AssetCombobox label="Activo" value={value} onChange={setValue} allowMarketSearch={allowMarketSearch} />
  );
}

function renderCombobox(allowMarketSearch = false) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  const invalidate = vi.spyOn(client, "invalidateQueries");
  render(
    <QueryClientProvider client={client}>
      <Harness allowMarketSearch={allowMarketSearch} />
    </QueryClientProvider>,
  );
  return { invalidate };
}

function type(value: string) {
  const input = screen.getByRole("combobox", { name: "Activo" });
  fireEvent.change(input, { target: { value } });
  return input;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("AssetCombobox: buscar en el mercado", () => {
  it("con resultados locales, la opción del mercado va la última", async () => {
    stubApi([asset]);
    renderCombobox(true);
    type("IWDA");
    const market = await screen.findByRole("option", { name: /Buscar «IWDA» en el mercado/ });
    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(2);
    expect(options[0]?.textContent).toContain("iShares Core MSCI World");
    expect(options[1]).toBe(market);
  });

  it("sin resultados locales es la única opción; con Intro da de alta y deja elegido el activo", async () => {
    let resolve: (r: Response) => void = () => {};
    const fetchMock = stubApi([], () => new Promise<Response>((r) => (resolve = r)));
    const { invalidate } = renderCombobox(true);
    const input = type("World");
    await screen.findByRole("option", { name: /Buscar «World» en el mercado/ });
    expect(screen.getAllByRole("option")).toHaveLength(1);
    expect(screen.getByRole("status").textContent).toContain("Puedes buscarlo en el mercado");

    fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "Enter" });
    await screen.findByRole("option", { name: /Buscando en el mercado…/ });
    expect(screen.getByRole("status").textContent).toBe("Buscando «World» en el mercado…");

    const post = fetchMock.mock.calls.find(([url]) => url === "/api/v1/assets")!;
    expect(post[1]?.method).toBe("POST");
    expect(JSON.parse(post[1]?.body as string)).toEqual({ query: "World" });

    resolve(json(asset, 201));
    const chosen = await screen.findByRole("group", { name: "Activo" });
    expect(chosen.textContent).toContain(asset.name);
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["assets", "lookup"] });
  });

  it("si el mercado no lo conoce, muestra el mensaje del backend sin cerrar el buscador", async () => {
    const message = "No encontramos «ZZZZ» en el mercado.";
    stubApi([], () => json({ code: "NOT_FOUND", message, details: {} }, 404));
    renderCombobox(true);
    type("ZZZZ");
    fireEvent.click(await screen.findByRole("option", { name: /Buscar «ZZZZ» en el mercado/ }));
    await waitFor(() => expect(screen.getByRole("status").textContent).toBe(message));
    expect(screen.getByRole("combobox", { name: "Activo" })).toBeTruthy();
    expect(screen.getByRole("option", { name: /Buscar «ZZZZ» en el mercado/ })).toBeTruthy();
  });

  it("sin allowMarketSearch no aparece la opción del mercado", async () => {
    const fetchMock = stubApi([]);
    renderCombobox();
    type("World");
    await waitFor(() =>
      expect(screen.getByRole("status").textContent).toBe("No hay activos que coincidan con «World»."),
    );
    expect(screen.queryByRole("option")).toBeNull();
    expect(fetchMock.mock.calls.some(([url]) => url === "/api/v1/assets")).toBe(false);
  });
});
