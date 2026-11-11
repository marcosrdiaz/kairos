import { expect, type APIRequestContext, type Locator, type Page } from "@playwright/test";

/** Ayudas del E2E del guion: lo que en la demo hace el presentador (reset, replay) y preguntar. */

const API = "/api/v1";

/** El evento que se lanza en directo en el paso 3 (como `make replay EVENT=nvda-2025-02`). */
export const LIVE_EVENT = "nvda-2025-02";
export const LIVE_EVENT_TITLE = /NVIDIA cae/;

/**
 * Un rango de impacto tal como lo pinta el frontend: «entre -349 € y -325 €». Entre la cifra y el
 * símbolo va un espacio de no separación (`Intl.NumberFormat`): `\s` cubre los dos.
 */
export const RANGE = /^entre\s-?[\d.]+(,\d+)?\s€\sy\s-?[\d.]+(,\d+)?\s€/;

/**
 * Órdenes de compraventa que ningún texto puede contener (regla 2 de `CLAUDE.md`). Más estrecho
 * que el guardián: aquí solo se comprueba que no se cuela nada evidente en la pantalla.
 */
export const ORDERS =
  /te recomiendo|te aconsejo|deber[ií]as (comprar|vender|invertir)|(^|[.!¡]\s*)(compra|vende|invierte)\b|es buen momento para/i;

/** `POST /demo/reset` con `preload`: BCE y petróleo ya ocurridos, Laura en Tranquilo (paso 1). */
export async function resetDemo(api: APIRequestContext): Promise<void> {
  const response = await api.post(`${API}/demo/reset`, { data: { preload: true } });
  expect(response.ok(), await response.text()).toBe(true);
}

/** `POST /demo/replay/{id}`: el evento llega en directo. */
export async function replay(api: APIRequestContext, eventId = LIVE_EVENT): Promise<void> {
  const response = await api.post(`${API}/demo/replay/${eventId}`);
  expect(response.ok(), await response.text()).toBe(true);
}

/**
 * Elige una opción de un grupo de radios. El `<input>` está oculto (`sr-only`) bajo su etiqueta,
 * que es lo que pulsa el usuario: se pulsa la etiqueta y se comprueba que el radio queda marcado.
 */
export async function choose(page: Page, group: string, option: string): Promise<void> {
  const radios = page.getByRole("group", { name: group });
  await radios.getByText(option, { exact: true }).click();
  await expect(radios.getByRole("radio", { name: option })).toBeChecked();
}

/** La tarjeta de estado de Inicio («Tu cartera hoy»): su nombre accesible cambia con la frase. */
export function statusCard(page: Page): Locator {
  return page.getByRole("region").filter({ hasText: "Tu cartera hoy" });
}

/**
 * Pregunta por escrito en el asistente (plan B de la voz, T2-14) y devuelve el turno ya
 * terminado: las frases y los botones «¿De dónde sale?» llegan al acabar el SSE.
 */
export async function ask(page: Page, question: string): Promise<Locator> {
  const input = page.getByRole("textbox", { name: "Escribe tu pregunta" });
  if (!(await input.isVisible())) {
    await page.getByRole("button", { name: /^Abrir el asistente/ }).click();
  }
  await input.fill(question);
  await page.getByRole("button", { name: "Enviar pregunta" }).click();
  const turn = page
    .getByRole("list", { name: "Conversación" })
    .getByRole("listitem")
    .filter({ hasText: question })
    .last();
  await expect(turn.getByRole("button", { name: /^¿De dónde sale\?/ }).first()).toBeVisible({
    timeout: 30_000,
  });
  return turn;
}

/**
 * Abre la tarjeta de una cifra (T5-18), de ahí la traza completa, y comprueba que trae entradas,
 * fórmula, resultado y fuentes.
 */
export async function expectTrace(page: Page, trigger: Locator): Promise<void> {
  await trigger.click();
  const card = page.getByRole("group", { name: "De dónde sale esta cifra" });
  await expect(card).toBeVisible();
  await card.getByRole("button", { name: "Ver el cálculo completo" }).click();
  await expect(card).toBeHidden();
  const trace = page.getByRole("dialog", { name: "¿De dónde sale esta cifra?" });
  await expect(trace).toBeVisible();
  for (const heading of ["Entradas", "Fórmula", "Resultado", "Fuentes"]) {
    await expect(trace.getByRole("heading", { name: heading, exact: true })).toBeVisible();
  }
  await trace.getByRole("button", { name: "Cerrar" }).click();
  await expect(trace).toBeHidden();
}
