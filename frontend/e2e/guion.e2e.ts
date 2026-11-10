import { expect, test } from "@playwright/test";
import {
  ask,
  choose,
  expectTrace,
  LIVE_EVENT_TITLE,
  ORDERS,
  RANGE,
  replay,
  resetDemo,
  statusCard,
} from "./demo";

/**
 * Guion de demo de 8 pasos (`docs/kairos-spec.md`, «Guion de demo») en el navegador, contra el
 * backend real en modo offline: datos de `data/`, reloj fijo, plantillas en vez de Claude y voz
 * mock. Cada test parte de `/demo/reset` con `preload`, como antes de un ensayo.
 *
 * Las cifras no se fijan aquí (las calibra T3-04): se comprueba que están, con su forma (€, %,
 * rango), su traza y sin órdenes de compraventa.
 */

test.beforeEach(async ({ request }) => {
  await resetDemo(request);
});

test("paso 1 · Laura arranca en Tranquilo, con sus precios y los avisos de IA", async ({ page }) => {
  await page.goto("/inicio");

  const status = statusCard(page);
  await expect(status).toContainText("Tranquilo");
  await expect(status.getByRole("heading", { level: 2 })).toContainText(/[\d.]+ euros/);
  await expect(page.getByRole("radio", { name: "Laura" })).toBeChecked();

  const assets = page.getByRole("region", { name: "Tus activos" });
  await expect(assets.getByRole("listitem").first()).toContainText(/\d\s(€|US\$)/);

  await expect(page.getByText(/usa inteligencia artificial.*No es asesoramiento/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Avisos, ninguno sin leer" })).toBeVisible();
});

test("paso 2 · radiografía: país y empresas mirando dentro de los fondos", async ({ page }) => {
  await page.goto("/panel");

  const exposure = page.getByRole("region", { name: "Exposición", exact: true });
  await expect(exposure.getByText("Mayor país: Estados Unidos")).toBeVisible();
  await expect(exposure.getByText("Tus 7 mayores empresas")).toBeVisible();
  const shares = exposure.getByRole("button", { name: /^\d{1,2},\d % ¿De dónde sale\?$/ });
  await expect(shares.first()).toBeVisible();
  await expect(
    exposure.getByRole("table", { name: /mayores empresas de la cartera/ }).getByRole("row"),
  ).not.toHaveCount(0);

  await expectTrace(page, shares.first());
});

test("paso 3 · el evento en directo pasa el widget a Atento y llega el aviso", async ({
  page,
  request,
}) => {
  await page.goto("/inicio");
  await expect(statusCard(page)).toContainText("Tranquilo");

  await replay(request);

  const notice = page.getByRole("link", { name: LIVE_EVENT_TITLE }).filter({
    hasText: "Aviso de Kairos",
  });
  await expect(notice).toBeVisible();
  await expect(notice).toHaveAccessibleName(/[\d.]+ euros menos/);
  await expect(notice).not.toHaveAccessibleName(ORDERS);
  await expect(statusCard(page)).toContainText("Atento");
  await expect(page.getByRole("button", { name: "Avisos, 1 sin leer" })).toBeVisible();

  // La pantalla de inicio del móvil simulada (widget, RF-13) dice lo mismo.
  await page.goto("/widget");
  await expect(page.getByText("Atento").first()).toBeVisible();
});

test("paso 4 y 8 · «¿Por qué ha bajado?» responde con la cadena y cifras trazables", async ({
  page,
  request,
}) => {
  await replay(request);
  await page.goto("/inicio");

  const turn = await ask(page, "¿Por qué ha bajado?");

  // Aviso de IA al empezar (AI Act art. 50) y el evento, con su impacto en euros.
  await expect(turn).toContainText("Soy el asistente de KAIROS, una IA");
  await expect(turn).toContainText(LIVE_EVENT_TITLE);
  await expect(turn).toContainText(/[\d.]+ euros/);
  await expect(turn).not.toContainText(ORDERS);

  await expectTrace(page, turn.getByRole("button", { name: /^¿De dónde sale\?/ }).first());
});

test("paso 5 · el panel traduce los eventos a la cartera, con riesgos y agenda", async ({
  page,
  request,
}) => {
  await replay(request);
  await page.goto("/panel");

  await expect(page.getByRole("region", { name: "Información, no asesoramiento" })).toBeVisible();

  const events = page.getByRole("region", { name: "Eventos", exact: true });
  const cards = events.getByRole("article");
  await expect(cards).toHaveCount(3);
  for (const card of await cards.all()) {
    await expect(card.getByRole("list", { name: "Cadena causal" })).toBeVisible();
    await expect(card.getByRole("button", { name: RANGE })).toBeVisible();
    await expect(card).toContainText(/Confianza (alta|media|baja)/);
    await expect(card).not.toContainText(ORDERS);
  }

  // Filtro por tipo: solo los resultados (NVIDIA).
  await choose(page, "Filtrar por tipo", "Resultados");
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toContainText(LIVE_EVENT_TITLE);

  await expectTrace(page, cards.first().getByRole("button", { name: RANGE }));

  for (const block of ["Exposición", "Radar", "Agenda"]) {
    const region = page.getByRole("region", { name: block, exact: true });
    await expect(region.getByRole("heading", { level: 3 }).first()).toBeVisible();
  }
});

test("paso 6 · la misma noticia, distinta en la cartera de Laura y en la de Javier", async ({
  page,
  request,
}) => {
  await replay(request);
  await page.goto("/panel");

  const nvidia = page
    .getByRole("region", { name: "Eventos", exact: true })
    .getByRole("article")
    .filter({ hasText: LIVE_EVENT_TITLE });
  const range = nvidia.getByRole("button", { name: RANGE });

  await expect(range).toBeVisible();
  const laura = { range: await range.textContent(), text: await nvidia.textContent() };

  await choose(page, "Cartera", "Javier");
  await expect(page).toHaveURL(/[?&]p=javier/);
  await expect(range).toBeVisible();
  await expect(range).not.toHaveText(laura.range ?? "");
  expect(await nvidia.textContent()).not.toBe(laura.text);
});

test("paso 7 · «¿Voy bien?» responde con la proyección frente al objetivo", async ({ page }) => {
  await page.goto("/inicio");

  const turn = await ask(page, "¿Voy bien?");

  await expect(turn).toContainText(/objetivo/);
  await expect(turn).toContainText(/[\d.]+ euros/);
  await expect(turn).not.toContainText(ORDERS);
  await expectTrace(page, turn.getByRole("button", { name: /^¿De dónde sale\?/ }).first());
});
