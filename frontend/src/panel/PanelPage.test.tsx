import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { Link, MemoryRouter, useLocation } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import bce from "../api/mocks/EventImpactOut.json";
import nvda from "../api/mocks/EventImpactOut.nvda.json";
import javier from "../api/mocks/PortfolioOut.javier.json";
import laura from "../api/mocks/PortfolioOut.json";
import agendaBce from "../api/mocks/AgendaItemOut.json";
import agendaDca from "../api/mocks/AgendaItemOut.dca.json";
import exposure from "../api/mocks/ExposureOut.json";
import history from "../api/mocks/PortfolioHistoryOut.json";
import plan from "../api/mocks/PlanOut.json";
import radar from "../api/mocks/RadarOut.json";
import status from "../api/mocks/StatusOut.json";
import { PanelPage } from "./PanelPage";

const EMPTY_RADAR = { items: [], calc_id: "calc_radar_vacio" };

const PORTFOLIOS = [
  { id: "laura", name: "Laura", profile: "dinamico" },
  { id: "javier", name: "Javier", profile: "moderado" },
];

const json = (body: unknown, code = 200) =>
  new Response(JSON.stringify(body), { status: code, headers: { "Content-Type": "application/json" } });

/** Backend falso: sirve cada ruta según la cartera pedida. `events` por cartera. */
function stubApi(
  events: Record<string, unknown[] | "error"> = { laura: [bce, nvda], javier: [nvda] },
  others: {
    exposure?: unknown;
    radar?: Record<string, unknown>;
    agenda?: unknown[];
    plan?: unknown;
    history?: (period: string) => unknown;
  } = {},
) {
  const radars = others.radar ?? { laura: radar, javier: EMPTY_RADAR };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/portfolios")) return json(PORTFOLIOS);
      const id = /portfolios\/(\w+)/.exec(url)?.[1] ?? "laura";
      if (url.includes("/status")) return json({ ...status, state: "atento" });
      if (url.includes("/history")) {
        const period = /period=(\w+)/.exec(url)?.[1] ?? "1m";
        return json(others.history ? others.history(period) : { ...history, period });
      }
      if (/\/plan$/.test(url)) {
        if (others.plan === "missing") return json({ code: "NOT_FOUND", message: "Sin plan" }, 404);
        return json(others.plan ?? plan);
      }
      if (url.includes("/agenda")) return json(others.agenda ?? [agendaDca, agendaBce]);
      if (url.includes("/exposure")) {
        return others.exposure === "error" ? json({ code: "INTERNAL" }, 500) : json(others.exposure ?? exposure);
      }
      if (url.includes("/radar")) return json(radars[id] ?? EMPTY_RADAR);
      if (url.includes("/events")) {
        const list = events[id];
        return list === "error" ? json({ code: "INTERNAL" }, 500) : json(list ?? []);
      }
      return json(id === "javier" ? javier : laura);
    }),
  );
}

function LocationProbe() {
  const { search } = useLocation();
  return <div data-testid="search">{search}</div>;
}

function renderPanel(path = "/panel?p=laura") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <PanelPage />
        <Link to="/panel?p=javier">Abrir panel de Javier</Link>
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("PanelPage · Resumen", () => {
  it("muestra la cabecera con cartera y subtítulo, y estira las tarjetas del resumen", async () => {
    stubApi();
    renderPanel();
    expect(await screen.findByRole("heading", { level: 1, name: "Panel de contexto" })).toBeTruthy();
    expect(
      screen.getByText("Datos, eventos y exposiciones que ayudan a entender tu cartera."),
    ).toBeTruthy();
    expect(
      await screen.findByText(
        (_, element) => element?.tagName === "P" && element.textContent === "Cartera: Laura",
      ),
    ).toBeTruthy();

    const wealth = (await screen.findByText("Patrimonio")).closest("section")!;
    const planCard = (await screen.findByRole("heading", { level: 3, name: "Tu plan" })).closest(
      "section",
    )!;
    expect(wealth.className).toContain("h-full");
    expect(planCard.className).toContain("h-full");
    expect(planCard.parentElement?.className).toContain("items-stretch");
    expect(wealth.querySelector("svg")?.parentElement?.className).toContain("text-chart-1");
    expect(screen.queryByRole("heading", { name: "¿Y si…?" })).toBeNull();
  });

  it("muestra patrimonio exacto con fecha, estado con palabra y posiciones con la fecha de su precio", async () => {
    stubApi();
    renderPanel();
    const dl = await screen.findByText("Patrimonio");
    expect(dl.parentElement?.textContent).toMatch(/34\.311,68\s€/);
    expect(dl.parentElement?.textContent).toMatch(/Valorado a/);
    expect(await screen.findByText("Atento")).toBeTruthy();
    const table = screen.getByRole("table", { name: /Posiciones de la cartera/ });
    const rows = within(table).getAllByRole("row");
    expect(rows.length).toBe(laura.positions.length + 1);
    // Fecha corta en la columna; la completa, en el title.
    const dates = within(table).getAllByText(/^6 nov\.?$/);
    expect(dates.length).toBeGreaterThan(0);
    expect(dates[0]!.getAttribute("title")).toBe("6 de noviembre de 2026");
    expect(table.querySelector("[data-calc-id]")).not.toBeNull();

    const positive = laura.positions.find((position) => !position.unrealized_pnl_eur.startsWith("-"))!;
    const positiveRow = within(table)
      .getAllByRole("row")
      .find((row) => row.textContent?.includes(positive.name))!;
    const positiveCells = within(positiveRow).getAllByRole("cell");
    const positivePnl = positiveCells[positiveCells.length - 1]!;
    expect(positivePnl.className).toContain("text-trend-up");
    expect(positivePnl.textContent).toMatch(/\+/);
  });

  it("marca la plusvalía negativa con color y conserva el signo", async () => {
    stubApi();
    renderPanel("/panel?p=javier");
    const table = await screen.findByRole("table", { name: /Posiciones de la cartera/ });
    const negative = javier.positions.find((position) => position.unrealized_pnl_eur.startsWith("-"))!;
    const row = within(table)
      .getAllByRole("row")
      .find((tableRow) => tableRow.textContent?.includes(negative.name))!;
    const cells = within(row).getAllByRole("cell");
    const pnl = cells[cells.length - 1]!;
    expect(pnl.className).toContain("text-trend-down");
    expect(pnl.textContent).toMatch(/-/);
  });

  it("el patrimonio cambia de periodo y muestra el valor inicial y las aportaciones del backend", async () => {
    const seen: string[] = [];
    stubApi(undefined, {
      history: (period) => {
        seen.push(period);
        return period === "1y"
          ? { ...history, period, start_value_eur: "28000.00", net_flows_eur: "0.00" }
          : { ...history, period };
      },
    });
    renderPanel();
    const card = (await screen.findByText("Patrimonio")).closest("section") as HTMLElement;
    expect(await within(card).findByText(/33\.410,25\s€/)).toBeTruthy();
    expect(within(card).getByText(/\+300,00\s€/)).toBeTruthy();
    expect((within(card).getByRole("radio", { name: "Último mes" }) as HTMLInputElement).checked).toBe(true);
    expect(within(card).queryByText(/periodo anterior/)).toBeNull();

    fireEvent.click(within(card).getByRole("radio", { name: "Último año" }));
    expect(await within(card).findByText(/28\.000,00\s€/)).toBeTruthy();
    expect(within(card).getByText(/sin aportaciones ni retiradas/)).toBeTruthy();
    expect(seen).toContain("1y");
    expect(within(card).getByText("Última semana")).toBeTruthy();
  });

  it("«Tu plan» compara el reparto con el objetivo y el margen, sin órdenes", async () => {
    stubApi(undefined, { plan: { ...plan, drift_equity: "0.12", drift_exceeded: true } });
    renderPanel();
    const card = (await screen.findByRole("heading", { level: 3, name: "Tu plan" })).closest("section") as HTMLElement;
    const bar = within(card).getByRole("progressbar", { name: "Renta variable" });
    expect(bar.getAttribute("aria-valuetext")).toMatch(/72,0\s%.*70\s%/);
    expect(within(card).getByText(/12,0 puntos por encima del objetivo/)).toBeTruthy();
    expect(within(card).getByText(/Fuera del margen de ±10\s%/)).toBeTruthy();
    expect(within(card).getByText(/150\.000\s€ en 2040/)).toBeTruthy();
    expect(card.querySelector("[data-calc-id]")).not.toBeNull();
    expect(card.textContent).not.toMatch(/compra|vende|deberías|te recomiendo/i);
  });

  it("sin plan, «Tu plan» lo dice sin inventar un reparto", async () => {
    stubApi(undefined, { plan: "missing" });
    renderPanel();
    expect(await screen.findByText(/aún no tiene un plan de inversión/)).toBeTruthy();
    expect(screen.queryByRole("progressbar", { name: "Renta variable" })).toBeNull();
  });

  it("deja el hueco de los avisos de T2-12", async () => {
    stubApi();
    const { container } = renderPanel();
    await screen.findByText("Patrimonio");
    expect(container.querySelector('[data-slot="panel-notices"]')).not.toBeNull();
  });
});

describe("PanelPage · Eventos", () => {
  it("pinta cada evento con cadena causal, rango y confianza, nunca cifra exacta", async () => {
    stubApi();
    renderPanel();
    expect(await screen.findByRole("heading", { level: 3, name: bce.title })).toBeTruthy();
    expect(screen.getAllByText(/entre -10\s€ y 190\s€/).length).toBe(1);
    expect(screen.getAllByText(/^Confianza (alta|media|baja)$/).length).toBe(2);
    expect(screen.getAllByRole("list", { name: "Cadena causal" }).length).toBe(2);
    expect(screen.queryByText(/90,00\s€/)).toBeNull();
    const loss = screen.getByRole("heading", { level: 3, name: nvda.title }).closest("article")!;
    expect(within(loss).getByText(/entre -620\s€ y -320\s€/).closest("dd")?.className).toContain(
      "text-trend-down",
    );
  });

  it("marca los rangos positivos y hace explícito el signo", async () => {
    const positive = { ...bce, low_eur: "5.00", impact_eur: "61.00", high_eur: "117.00" };
    stubApi({ laura: [positive], javier: [] });
    renderPanel();
    const range = await screen.findByText(/entre \+5\s€ y \+117\s€/);
    expect(range.closest("dd")?.className).toContain("text-trend-up");
  });

  it("sin eventos, lo dice sin inventar cifras", async () => {
    stubApi({ laura: [], javier: [] });
    renderPanel();
    expect(await screen.findByText(/Ningún evento reciente afecta/)).toBeTruthy();
  });

  it("si falla el backend, muestra un estado vacío honesto", async () => {
    stubApi({ laura: "error", javier: [] });
    renderPanel();
    expect(await screen.findByText(/no podemos mostrar los eventos/)).toBeTruthy();
  });
});

describe("PanelPage · cambio de cartera", () => {
  it("al abrir el panel para Javier cambian los datos y se mantiene ?p=", async () => {
    stubApi();
    renderPanel();
    await screen.findByRole("heading", { level: 3, name: bce.title });
    fireEvent.click(screen.getByRole("link", { name: "Abrir panel de Javier" }));
    expect(screen.getByTestId("search").textContent).toBe("?p=javier");
    await waitFor(() => expect(screen.queryByRole("heading", { level: 3, name: bce.title })).toBeNull());
    expect(await screen.findByRole("heading", { level: 3, name: nvda.title })).toBeTruthy();
    expect((await screen.findByText("Patrimonio")).parentElement?.textContent).toMatch(/\d/);
    expect(screen.getByText("Mostrando la cartera de Javier")).toBeTruthy();
  });
});

describe("PanelPage · rango colapsado", () => {
  it("si low == high muestra «≈ importe» y no «entre X y X»", async () => {
    const collapsed = { ...bce, low_eur: "-223.69", impact_eur: "-223.69", high_eur: "-223.69" };
    stubApi({ laura: [collapsed], javier: [] });
    renderPanel();
    expect(await screen.findByText(/^≈ -224\s€$/)).toBeTruthy();
    expect(screen.queryByText(/entre -224/)).toBeNull();
  });
});

describe("PanelPage · Exposición", () => {
  it("muestra la radiografía, los repartos y las mayores empresas con sus activos", async () => {
    stubApi();
    renderPanel();
    expect(await screen.findByRole("heading", { level: 2, name: "Exposición" })).toBeTruthy();
    expect(await screen.findByText(/Mayor país: Estados Unidos/)).toBeTruthy();
    for (const t of ["Por país", "Por sector", "Por divisa"]) {
      expect(screen.getByRole("region", { name: t })).toBeTruthy();
    }
    const list = await screen.findByRole("list", { name: /Diez mayores empresas/ });
    expect(within(list).getByText(exposure.top_companies[0]!.name)).toBeTruthy();
    // Barras relativas a la mayor: la primera llena el carril (calc con las fracciones tal cual).
    const companyBars = list.querySelectorAll("li span[style]");
    expect(companyBars[0]?.getAttribute("style")).toMatch(/width:\s*calc\(100%\)/);
    expect(companyBars[0]?.className).toContain("bg-chart-1");
    expect(companyBars[1]?.className).toContain("bg-chart-2");
    expect(screen.getByText(/cubierta: 94,0\s%/)).toBeTruthy();
    expect(document.querySelector("#exposicion [data-calc-id]")).not.toBeNull();
  });

  it("la anchura de las barras sale de la fracción del backend, sin pasarla a number", async () => {
    stubApi();
    renderPanel();
    const country = await screen.findByRole("region", { name: "Por país" });
    const bar = country.querySelector<HTMLElement>("li span[style]");
    // jsdom resuelve el calc(); en el navegador es calc(0.61 * 100%).
    expect(bar?.getAttribute("style")).toMatch(/width:\s*calc\(61%\)/);
    expect(bar?.className).toContain("bg-chart-1");
  });

  it("si falla, estado vacío honesto", async () => {
    stubApi(undefined, { exposure: "error" });
    renderPanel();
    expect(await screen.findByText(/no podemos mostrar la exposición/)).toBeTruthy();
  });
});

describe("PanelPage · Radar", () => {
  it("riesgo y oportunidad con su palabra, su importe y la regla del usuario", async () => {
    stubApi();
    renderPanel();
    const cheaper = await screen.findByRole("heading", { level: 3, name: radar.items[1]!.title });
    const card = cheaper.closest("li")!;
    expect(within(card).getByText("Oportunidad")).toBeTruthy();
    expect(within(card).getByText("tu plan de aportaciones")).toBeTruthy();
    expect(within(card).getByText(/210\s€/)).toBeTruthy();
    const risk = screen.getByRole("heading", { level: 3, name: radar.items[0]!.title }).closest("li")!;
    expect(within(risk).getByText("Riesgo")).toBeTruthy();
    expect(card.querySelector("[data-calc-id]")).not.toBeNull();
  });

  it("sin nada que destacar (Javier), lo dice sin inventar cifras", async () => {
    stubApi();
    renderPanel("/panel?p=javier");
    expect(await screen.findByText(/el radar no ve riesgos ni oportunidades/)).toBeTruthy();
  });
});

describe("PanelPage · Agenda", () => {
  it("muestra lo que da el backend, ordenado por fecha, con lo expuesto", async () => {
    stubApi();
    renderPanel();
    const bceRow = (await screen.findByRole("heading", { level: 3, name: agendaBce.title })).closest("li")!;
    const dcaRow = screen.getByRole("heading", { level: 3, name: agendaDca.title }).closest("li")!;
    expect(bceRow.textContent).toMatch(/los tipos de interés del euro: un 28,5\s%/);
    expect(within(bceRow).getByText(/9777\s€/)).toBeTruthy();
    expect(within(dcaRow).getByText("Aportación prevista")).toBeTruthy();
    // 12 nov antes que 5 dic, aunque el backend los mande al revés
    expect(bceRow.compareDocumentPosition(dcaRow) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(bceRow.querySelector("[data-calc-id]")).not.toBeNull();
  });

  it("agenda vacía: lo dice, sin inventar", async () => {
    stubApi(undefined, { agenda: [] });
    renderPanel();
    expect(await screen.findByText(/No hay nada previsto/)).toBeTruthy();
  });
});

describe("PanelPage · filtro de eventos", () => {
  it("filtra por tipo, cuenta lo que se ve y vuelve a Todos", async () => {
    stubApi();
    renderPanel();
    await screen.findByRole("heading", { level: 3, name: bce.title });
    const group = screen.getByRole("group", { name: "Filtrar por tipo" });
    expect(within(group).getAllByRole("radio").map((r) => (r as HTMLInputElement).value)).toEqual([
      "all",
      "central_bank",
      "earnings",
    ]);
    expect(within(group).getByRole("status").textContent).toBe("2 eventos");

    fireEvent.click(within(group).getByRole("radio", { name: "Resultados" }));
    expect(screen.queryByRole("heading", { level: 3, name: bce.title })).toBeNull();
    expect(screen.getByRole("heading", { level: 3, name: nvda.title })).toBeTruthy();
    expect(within(group).getByRole("status").textContent).toBe("1 de 2");

    fireEvent.click(within(group).getByRole("radio", { name: "Todos" }));
    expect(screen.getByRole("heading", { level: 3, name: bce.title })).toBeTruthy();
  });

  it("con un solo tipo de evento no hay filtro que ofrecer", async () => {
    stubApi({ laura: [bce], javier: [] });
    renderPanel();
    await screen.findByRole("heading", { level: 3, name: bce.title });
    expect(screen.queryByRole("group", { name: "Filtrar por tipo" })).toBeNull();
  });

  it("al cambiar de cartera el filtro vuelve a Todos", async () => {
    stubApi({ laura: [bce, nvda], javier: [bce, nvda] });
    renderPanel();
    await screen.findByRole("heading", { level: 3, name: bce.title });
    fireEvent.click(screen.getByRole("radio", { name: "Resultados" }));
    fireEvent.click(screen.getByRole("link", { name: "Abrir panel de Javier" }));
    expect(await screen.findByRole("heading", { level: 3, name: bce.title })).toBeTruthy();
    expect((screen.getByRole("radio", { name: "Todos" }) as HTMLInputElement).checked).toBe(true);
  });
});

describe("PanelPage · accesibilidad", () => {
  it("permite recorrer las chips con flechas en ambas direcciones", async () => {
    stubApi();
    renderPanel();
    const nav = screen.getByRole("navigation", { name: "Bloques del panel" });
    const rail = nav.querySelector("ul")!;
    Object.defineProperty(rail, "clientWidth", { configurable: true, value: 250 });
    Object.defineProperty(rail, "scrollWidth", { configurable: true, value: 900 });
    const scrollBy = vi.fn();
    Object.defineProperty(rail, "scrollBy", { configurable: true, value: scrollBy });
    fireEvent(window, new Event("resize"));

    const next = screen.getByRole<HTMLButtonElement>("button", {
      name: "Desplazar bloques a la derecha",
    });
    const previous = screen.getByRole<HTMLButtonElement>("button", {
      name: "Desplazar bloques a la izquierda",
    });
    await waitFor(() => expect(next.disabled).toBe(false));
    expect(previous.disabled).toBe(true);
    expect(next.getAttribute("aria-controls")).toBe(rail.id);
    fireEvent.click(next);
    expect(scrollBy).toHaveBeenCalledWith({ left: 180, behavior: "smooth" });

    let scrollLeft = 0;
    Object.defineProperty(rail, "scrollLeft", {
      configurable: true,
      get: () => scrollLeft,
      set: (value: number) => {
        scrollLeft = value;
      },
    });
    scrollLeft = 200;
    fireEvent.scroll(rail);
    await waitFor(() => expect(previous.disabled).toBe(false));
    fireEvent.click(previous);
    expect(scrollBy).toHaveBeenLastCalledWith({ left: -180, behavior: "smooth" });
  });

  it("tiene un único h1; el enlace de salto lo aporta AppShell", async () => {
    stubApi();
    renderPanel();
    await screen.findByText("Patrimonio");
    expect(screen.getAllByRole("heading", { level: 1 }).length).toBe(1);
  });

  it("cada bloque es una región con nombre y la cabecera enlaza a todos", async () => {
    stubApi();
    renderPanel();
    await screen.findByText("Patrimonio");
    const nav = screen.getByRole("navigation", { name: "Bloques del panel" });
    for (const id of ["resumen", "eventos", "exposicion", "radar", "agenda"]) {
      expect(nav.querySelector(`a[href="#${id}"]`)).not.toBeNull();
      expect(document.getElementById(id)?.getAttribute("aria-labelledby")).toBe(`${id}-title`);
    }
    expect(nav.querySelector('a[href="#escenarios"]')).toBeNull();
  });
});
