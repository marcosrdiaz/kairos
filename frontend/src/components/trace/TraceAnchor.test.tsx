import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { TraceOut } from "../../api/generated/schema";
import traceMock from "../../api/mocks/TraceOut.json";
import { TraceFigure } from "./TraceFigure";
import { TraceLink } from "./TraceLink";
import { TraceProvider } from "./TraceProvider";

/**
 * Dónde se abre la tarjeta «¿De dónde sale?» en una pantalla de escritorio de 1440 × 900 con el
 * asistente (T5-18, TD-13). jsdom no calcula posiciones: cada elemento clave devuelve el
 * rectángulo que tendría en `AppShell` y la cifra, el que fija cada test.
 */

const ROOT = { ...(traceMock as unknown as TraceOut), calc_id: "calc_root" };
const CARD = { name: "De dónde sale esta cifra" } as const;

type Rect = [left: number, top: number, right: number, bottom: number];
const asRect = ([left, top, right, bottom]: Rect): DOMRect =>
  ({ left, top, right, bottom, x: left, y: top, width: right - left, height: bottom - top }) as DOMRect;

const rects: Record<"anchor" | "main" | "chat" | "launcher", Rect> = {
  anchor: [400, 400, 480, 424],
  main: [304, 0, 1440, 900],
  chat: [1010, 0, 1440, 900],
  launcher: [1324, 784, 1412, 872],
};

function stubLayout() {
  Object.defineProperty(window, "innerWidth", { value: 1440, configurable: true });
  Object.defineProperty(window, "innerHeight", { value: 900, configurable: true });
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
    if (this.id === "contenido") return asRect(rects.main);
    if (this.id === "asistente") return asRect(rects.chat);
    if (this.id === "chat-launcher") return asRect(rects.launcher);
    if (this.dataset.calcId) return asRect(rects.anchor);
    return asRect([0, 0, 0, 0]);
  });
}

function stubTrace() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify(ROOT), { headers: { "Content-Type": "application/json" } })),
  );
}

function Providers({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={client}>
      <TraceProvider>{children}</TraceProvider>
    </QueryClientProvider>
  );
}

/** Monta `AppShell` en pequeño: contenido, asistente y botón flotante con los ids de verdad. */
function shell() {
  document.body.innerHTML =
    '<main id="contenido"><div id="en-contenido"></div></main>' +
    '<aside id="asistente"><div id="en-asistente"></div></aside>' +
    '<button id="chat-launcher" type="button">Abrir el asistente</button>';
  return {
    content: document.getElementById("en-contenido") as HTMLElement,
    chat: document.getElementById("en-asistente") as HTMLElement,
  };
}

beforeEach(() => {
  rects.main = [304, 0, 1440, 900];
  stubLayout();
  stubTrace();
});

afterEach(() => {
  cleanup();
  document.body.innerHTML = "";
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("tarjeta de una cifra en el panel del asistente (escritorio)", () => {
  it("no se cierra al abrirse: el panel del asistente cuenta como área visible", async () => {
    const { chat } = shell();
    rects.main = [304, 0, 1010, 900]; // con el asistente abierto, el contenido se estrecha
    rects.anchor = [1060, 400, 1200, 430]; // dentro de la columna del chat
    render(
      <Providers>
        <TraceLink calcId="calc_root" label="¿De dónde sale? (1)" />
      </Providers>,
      { container: chat },
    );
    const trigger = screen.getByRole("button", { name: "¿De dónde sale? (1)" });
    fireEvent.click(trigger);

    const card = await screen.findByRole("group", CARD);
    expect(trigger.getAttribute("aria-expanded")).toBe("true");
    // Dentro del panel (1010 a 1440), no encima del contenido.
    expect(Number.parseFloat(card.style.left)).toBeGreaterThanOrEqual(1010);
  });
});

describe("tarjeta de una cifra en la franja inferior de la pantalla", () => {
  it("abre, y por encima de la cifra, con la cifra a 860 px (por debajo del botón flotante)", async () => {
    const { content } = shell();
    rects.anchor = [400, 860, 480, 903];
    render(
      <Providers>
        <TraceFigure calcId="calc_root">100 €</TraceFigure>
      </Providers>,
      { container: content },
    );
    fireEvent.click(screen.getByRole("button", { name: /De dónde sale/ }));

    const card = await screen.findByRole("group", CARD);
    await waitFor(() => expect(card.style.top).not.toBe(""));
    expect(Number.parseFloat(card.style.top)).toBeLessThan(860);
  });

  it("no se queda sin abrir una cifra a la altura del botón, y no se solapa con él", async () => {
    const { content } = shell();
    rects.anchor = [1300, 800, 1380, 824]; // justo encima del botón, en su columna
    render(
      <Providers>
        <TraceFigure calcId="calc_root">100 €</TraceFigure>
      </Providers>,
      { container: content },
    );
    fireEvent.click(screen.getByRole("button", { name: /De dónde sale/ }));

    const card = await screen.findByRole("group", CARD);
    const left = Number.parseFloat(card.style.left);
    const width = Number.parseFloat(card.style.width);
    // La tarjeta queda a la izquierda del botón flotante (que empieza en 1324).
    expect(left + width).toBeLessThanOrEqual(rects.launcher[0]);
  });
});
