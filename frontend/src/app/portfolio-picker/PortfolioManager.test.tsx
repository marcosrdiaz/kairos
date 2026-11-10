import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useStatus } from "../../api/hooks/useStatus";
import { FirstRunGate } from "../onboarding/FirstRunGate";
import { PortfolioManager } from "./PortfolioManager";
import { PortfolioPicker } from "./PortfolioPicker";
import { PORTFOLIO_STORAGE_KEY } from "./storedPortfolio";
import { usePortfolioId } from "./usePortfolioId";

type Summary = { id: string; name: string; kind: string; risk_profile: string; profile: string };
type FetchArgs = [string, RequestInit?];

const p = (id: string, name: string, kind: string): Summary => ({
  id,
  name,
  kind,
  risk_profile: "moderado",
  profile: "moderado",
});

const THREE = () => [p("personal", "Personal", "personal"), p("negocio", "Negocio", "business"), p("hijos", "Hijos", "family")];

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

/** Backend falso con estado: lista, crea, renombra y borra carteras; `/status` responde por id. */
function stubApi(list: Summary[]) {
  const fetchMock = vi.fn(async (...[url, init]: FetchArgs) => {
    const method = init?.method ?? "GET";
    if (url === "/api/v1/portfolios" && method === "GET") return json(list);
    if (url === "/api/v1/portfolios" && method === "POST") {
      const body = JSON.parse(String(init?.body)) as { name: string; kind: string };
      const created = p("nueva", body.name, body.kind);
      list.push(created);
      return json(created, 201);
    }
    if (url === "/api/v1/portfolios/import" && method === "POST") {
      const body = JSON.parse(String(init?.body)) as { name: string; kind: string };
      const created = p("importada", body.name, body.kind);
      list.push(created);
      return json({ dry_run: false, portfolio: created, positions: [] }, 201);
    }
    const one = /^\/api\/v1\/portfolios\/([^/]+)$/.exec(url);
    if (one) {
      const idx = list.findIndex((x) => x.id === one[1]);
      if (idx < 0) return json({ code: "NOT_FOUND" }, 404);
      if (method === "DELETE") {
        list.splice(idx, 1);
        return new Response(null, { status: 204 });
      }
      if (method === "PATCH") {
        list[idx] = { ...list[idx]!, ...(JSON.parse(String(init?.body)) as object) };
        return json(list[idx]);
      }
    }
    const status = /^\/api\/v1\/portfolios\/([^/]+)\/status$/.exec(url);
    if (status) return json({ portfolio_id: status[1] });
    return json({ code: "NOT_FOUND" }, 404);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** Una pantalla cualquiera: enseña qué cartera usa y de cuál le llegan los datos. */
function ScreenProbe() {
  const [id] = usePortfolioId();
  const { data } = useStatus(id);
  const { search } = useLocation();
  return (
    <>
      <p data-testid="search">{search}</p>
      <p data-testid="data">{(data as { portfolio_id?: string } | undefined)?.portfolio_id ?? ""}</p>
    </>
  );
}

function renderApp(path = "/cartera") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route
            path="*"
            element={
              <FirstRunGate>
                <PortfolioPicker />
                <PortfolioManager />
                <ScreenProbe />
              </FirstRunGate>
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const param = () => new URLSearchParams(screen.getByTestId("search").textContent ?? "").get("p");

beforeEach(() => {
  localStorage.clear();
  HTMLDialogElement.prototype.showModal = function showModal() {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function close() {
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  };
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function deleteFlow(name: string) {
  fireEvent.click(await screen.findByRole("button", { name: `Borrar «${name}»` }));
  const dialog = await screen.findByRole("alertdialog", { name: `¿Borrar «${name}»?` });
  expect(document.activeElement).toBe(screen.getByRole("button", { name: "Cancelar" }));
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "Sí, borrar" }));
  });
  return dialog;
}

describe("PortfolioManager", () => {
  it("lista las carteras con su tipo y cambia los datos al elegir otra", async () => {
    stubApi(THREE());
    renderApp("/cartera?p=personal");
    expect(await screen.findByRole("radio", { name: "Negocio" })).toBeTruthy();
    expect(screen.getByRole("radio", { name: "Hijos, Familia" })).toBeTruthy();
    await waitFor(() => expect(screen.getByTestId("data").textContent).toBe("personal"));

    fireEvent.click(screen.getByRole("radio", { name: "Hijos, Familia" }));
    expect(param()).toBe("hijos");
    await waitFor(() => expect(screen.getByTestId("data").textContent).toBe("hijos"));
    expect(localStorage.getItem(PORTFOLIO_STORAGE_KEY)).toBe("hijos");
  });

  it("sin ?p= abre la última cartera elegida en este navegador", async () => {
    localStorage.setItem(PORTFOLIO_STORAGE_KEY, "negocio");
    stubApi(THREE());
    renderApp();
    await waitFor(() => expect(param()).toBe("negocio"));
    expect(((await screen.findByRole("radio", { name: "Negocio" })) as HTMLInputElement).checked).toBe(true);
  });

  it("con un ?p= que ya no existe, pasa a la primera cartera", async () => {
    stubApi(THREE());
    renderApp("/cartera?p=borrada");
    await waitFor(() => expect(param()).toBe("personal"));
  });

  it("«Nueva cartera» crea una y la deja elegida", async () => {
    const fetchMock = stubApi(THREE());
    renderApp("/cartera?p=personal");
    fireEvent.click(await screen.findByRole("button", { name: "Nueva cartera" }));
    await waitFor(() =>
      expect(document.activeElement).toBe(screen.getByRole("heading", { name: "Nueva cartera" })),
    );
    fireEvent.change(screen.getByRole("textbox", { name: "Nombre de la cartera" }), { target: { value: "Ahorro casa" } });
    fireEvent.click(screen.getByRole("radio", { name: /^Otra/ }));
    fireEvent.click(screen.getByRole("radio", { name: /Moderado/ }));
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));

    const step2 = await screen.findByRole("heading", { name: "Añade los activos de «Ahorro casa»" });
    await waitFor(() => expect(document.activeElement).toBe(step2));
    expect(screen.queryByRole("button", { name: "Cancelar" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Terminar" }));

    expect(await screen.findByText(/Cartera «Ahorro casa» creada/)).toBeTruthy();
    await waitFor(() => expect(param()).toBe("nueva"));
    const radio = screen.getByRole("radio", { name: "Ahorro casa, Otra" }) as HTMLInputElement;
    expect(radio.checked).toBe(true);
    await waitFor(() => expect(screen.getByTestId("data").textContent).toBe("nueva"));
    const call = fetchMock.mock.calls.find(([u, i]) => u === "/api/v1/portfolios" && i?.method === "POST");
    expect(JSON.parse(String(call?.[1]?.body))).toEqual({ name: "Ahorro casa", kind: "other", risk_profile: "moderado" });
  });

  it("«Nueva cartera» con CSV en el paso 2: sustituye la vacía por la importada y la deja elegida", async () => {
    const list = THREE();
    const fetchMock = stubApi(list);
    renderApp("/cartera?p=personal");
    fireEvent.click(await screen.findByRole("button", { name: "Nueva cartera" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Nombre de la cartera" }), { target: { value: "Ahorro casa" } });
    fireEvent.click(screen.getByRole("radio", { name: /Moderado/ }));
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
    await screen.findByRole("heading", { name: "Añade los activos de «Ahorro casa»" });

    fireEvent.click(screen.getByRole("button", { name: "Importar un CSV" }));
    const file = new File(["asset,units,avg_cost_eur\nIWDA,3,90\n"], "cartera.csv", { type: "text/csv" });
    fireEvent.change(screen.getByLabelText("Fichero CSV"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Importar" }));

    expect(await screen.findByText("Hemos importado 0 posiciones en «Ahorro casa».")).toBeTruthy();
    expect(fetchMock.mock.calls.find(([, i]) => i?.method === "DELETE")?.[0]).toBe("/api/v1/portfolios/nueva");
    expect(list.map((x) => x.id)).not.toContain("nueva");
    fireEvent.click(screen.getByRole("button", { name: "Terminar" }));

    expect(await screen.findByText(/Cartera «Ahorro casa» importada/)).toBeTruthy();
    await waitFor(() => expect(param()).toBe("importada"));
  });

  it("renombra una cartera con PATCH y lo anuncia", async () => {
    const fetchMock = stubApi(THREE());
    renderApp("/cartera?p=personal");
    fireEvent.click(await screen.findByRole("button", { name: "Renombrar «Hijos»" }));
    const input = screen.getByRole("textbox", { name: "Nuevo nombre de «Hijos»" });
    await waitFor(() => expect(document.activeElement).toBe(input));
    fireEvent.change(input, { target: { value: "Lucía y Pablo" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByText("«Hijos» ahora se llama «Lucía y Pablo».")).toBeTruthy();
    expect(screen.getByRole("radio", { name: "Lucía y Pablo, Familia" })).toBeTruthy();
    const call = fetchMock.mock.calls.find(([, i]) => i?.method === "PATCH");
    expect(call?.[0]).toBe("/api/v1/portfolios/hijos");
    expect(JSON.parse(String(call?.[1]?.body))).toEqual({ name: "Lucía y Pablo" });
    await waitFor(() =>
      expect(document.activeElement).toBe(screen.getByRole("button", { name: "Renombrar «Lucía y Pablo»" })),
    );
  });

  it("cancelar el borrado no llama a la API", async () => {
    const fetchMock = stubApi(THREE());
    renderApp("/cartera?p=personal");
    fireEvent.click(await screen.findByRole("button", { name: "Borrar «Negocio»" }));
    await screen.findByRole("alertdialog");
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(fetchMock.mock.calls.some(([, i]) => i?.method === "DELETE")).toBe(false);
  });

  it("borrar la elegida pasa a otra y sus datos", async () => {
    const fetchMock = stubApi(THREE());
    renderApp("/cartera?p=negocio");
    await waitFor(() => expect(screen.getByTestId("data").textContent).toBe("negocio"));
    await deleteFlow("Negocio");

    expect(await screen.findByText("Cartera «Negocio» borrada. Ahora estás viendo «Personal».")).toBeTruthy();
    expect(param()).toBe("personal");
    await waitFor(() => expect(screen.getByTestId("data").textContent).toBe("personal"));
    expect(screen.queryByRole("radio", { name: "Negocio" })).toBeNull();
    expect(localStorage.getItem(PORTFOLIO_STORAGE_KEY)).toBe("personal");
    const call = fetchMock.mock.calls.find(([, i]) => i?.method === "DELETE");
    expect(call?.[0]).toBe("/api/v1/portfolios/negocio");
  });

  it("borrar la última vuelve al asistente de primer uso", async () => {
    stubApi([p("personal", "Personal", "personal")]);
    renderApp("/cartera?p=personal");
    await deleteFlow("Personal");
    expect(await screen.findByRole("heading", { name: "Crea tu primera cartera" })).toBeTruthy();
    expect(screen.queryByTestId("search")).toBeNull();
  });
});
