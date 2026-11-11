import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { AlertOut, StatusOut } from "../api/generated/schema";
import { POLL_INTERVAL_MS } from "../api/hooks/polling";
import alertExample from "../api/mocks/AlertOut.json";
import atento from "../api/mocks/StatusOut.json";
import tranquilo from "../api/mocks/StatusOut.tranquilo.json";
import { InicioPage } from "../app/InicioPage";
import { PhoneHomePage } from "./PhoneHomePage";

const ALERT = alertExample as AlertOut;

let status: StatusOut;
let alerts: AlertOut[];
let failing: boolean;

function json(body: unknown, code = 200): Response {
  return new Response(JSON.stringify(body), {
    status: code,
    headers: { "Content-Type": "application/json" },
  });
}

function backend(input: RequestInfo | URL): Promise<Response> {
  const url = String(input);
  if (failing) return Promise.resolve(json({ code: "UPSTREAM_UNAVAILABLE" }, 503));
  if (url.endsWith("/status")) return Promise.resolve(json(status));
  if (url.endsWith("/alerts")) return Promise.resolve(json(alerts));
  return Promise.resolve(json([]));
}

/** Avanza `ms` y da un margen para que la respuesta se procese y se pinte. */
async function tick(ms = 0): Promise<void> {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
    await vi.advanceTimersByTimeAsync(50);
  });
}

function show(page: React.ReactNode, entry = "/widget?p=laura"): void {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[entry]}>{page}</MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal("fetch", vi.fn(backend));
  sessionStorage.clear();
  status = tranquilo as StatusOut;
  alerts = [];
  failing = false;
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("polling de /status y /alerts", () => {
  it("consulta cada 5 s", () => {
    expect(POLL_INTERVAL_MS).toBe(5_000);
  });

  it("el widget cambia solo tras un replay y llega el aviso con los euros", async () => {
    show(<PhoneHomePage />);
    await tick();
    expect(screen.getByRole("link", { name: /Tranquilo/ })).toBeTruthy();
    expect(screen.queryByText(ALERT.message)).toBeNull();

    status = atento as StatusOut;
    alerts = [ALERT];
    await tick(POLL_INTERVAL_MS);

    expect(screen.getByRole("link", { name: /Atento/ })).toBeTruthy();
    expect(screen.getByText(ALERT.message)).toBeTruthy();
  });

  it("si falla un sondeo mantiene los últimos datos y no muestra error", async () => {
    show(<PhoneHomePage />);
    await tick();
    failing = true;
    await tick(POLL_INTERVAL_MS);
    expect(screen.getByRole("link", { name: /Tranquilo/ })).toBeTruthy();
    expect(screen.queryByText(/no podemos mostrar/)).toBeNull();
  });

  it("si falla la primera lectura sí muestra el error", async () => {
    failing = true;
    show(<PhoneHomePage />);
    await tick();
    expect(screen.getByText(/no podemos mostrar/)).toBeTruthy();
  });

  it("deja de consultar al salir de la pantalla", async () => {
    show(<PhoneHomePage />);
    await tick();
    cleanup();
    const calls = vi.mocked(fetch).mock.calls.length;
    await tick(POLL_INTERVAL_MS * 3);
    expect(vi.mocked(fetch).mock.calls.length).toBe(calls);
  });
});

describe("aviso en pantalla de inicio", () => {
  it("no sale en Inicio de la app: los avisos van a la campana (TD-04)", async () => {
    alerts = [ALERT];
    show(<InicioPage />, "/inicio?p=laura");
    await tick();
    expect(screen.queryByText(ALERT.message)).toBeNull();
    expect(screen.queryByText("Aviso de Kairos")).toBeNull();
  });

  it("muestra solo el más reciente", async () => {
    alerts = [ALERT, { ...ALERT, id: "alr_antiguo", message: "Aviso antiguo." }];
    show(<PhoneHomePage />);
    await tick();
    expect(screen.getByText(ALERT.message)).toBeTruthy();
    expect(screen.queryByText("Aviso antiguo.")).toBeNull();
  });

  it("al cerrarlo no vuelve con el siguiente sondeo ni al volver a la pantalla", async () => {
    alerts = [ALERT];
    show(<PhoneHomePage />);
    await tick();
    fireEvent.click(screen.getByRole("button", { name: "Cerrar aviso" }));
    expect(screen.queryByText(ALERT.message)).toBeNull();
    await tick(POLL_INTERVAL_MS);
    expect(screen.queryByText(ALERT.message)).toBeNull();
    cleanup();
    show(<PhoneHomePage />);
    await tick();
    expect(screen.queryByText(ALERT.message)).toBeNull();
  });

  it("un aviso nuevo aparece aunque se cerrara el anterior", async () => {
    alerts = [ALERT];
    show(<PhoneHomePage />);
    await tick();
    fireEvent.click(screen.getByRole("button", { name: "Cerrar aviso" }));
    alerts = [{ ...ALERT, id: "alr_nuevo", message: "Aviso nuevo." }, ALERT];
    await tick(POLL_INTERVAL_MS);
    expect(screen.getByText("Aviso nuevo.")).toBeTruthy();
  });

  it("el anuncio al lector de pantalla está montado antes de que llegue el aviso", async () => {
    const { container } = render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter initialEntries={["/widget?p=laura"]}>
          <PhoneHomePage />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    await tick();
    expect(container.querySelector('[data-testid="alert-notice"][aria-live="polite"]')).toBeTruthy();
  });
});
