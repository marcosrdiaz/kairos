import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import type { NewsEstimateOut, NewsItemOut } from "../../api/generated/schema";
import estimated from "../../api/mocks/NewsItemOut.json";
import notRelevant from "../../api/mocks/NewsItemOut.not_relevant.json";
import pending from "../../api/mocks/NewsItemOut.pending.json";
import { NewsCard } from "./NewsCard";
import { eurRangeText, horizonText, methodText } from "./labels";

afterEach(cleanup);

const NVDA = estimated as NewsItemOut;

describe("NewsCard", () => {
  it("empieza por el efecto en la cartera: rango, plazo, tipo de cifra y confianza", () => {
    render(<NewsCard item={NVDA} />);
    const article = screen.getByRole("article", { name: NVDA.title });
    const effect = article.querySelector("p.text-lg");
    expect(effect?.textContent).toMatch(
      /Tu cartera podría moverse entre -270\s€ y -110\s€ en las próximas 5 sesiones\./,
    );
    expect(screen.getByText("Estimado")).toBeTruthy();
    expect(screen.getByText("Confianza media")).toBeTruthy();
    expect(screen.getByText(/entre -0,6\s% y -0,3\s%/)).toBeTruthy();
    expect(screen.getByText(/Según 8 casos parecidos del histórico/)).toBeTruthy();
    // La cifra lleva su calc_id para «¿De dónde sale?».
    expect(article.querySelector(`[data-calc-id="${NVDA.estimate!.calc_id}"]`)).not.toBeNull();
  });

  it("dice desde cuándo se nota en cada posición", () => {
    render(<NewsCard item={NVDA} />);
    expect(screen.getByText(/Se nota en la sesión · desde el 27 de febrero de 2025/)).toBeTruthy();
    expect(
      screen.getByText(/Se nota con el siguiente valor liquidativo · desde el 28 de febrero/),
    ).toBeTruthy();
  });

  it("enseña por qué afecta y enlaza la fuente en otra pestaña", () => {
    render(<NewsCard item={NVDA} />);
    expect(screen.getByRole("heading", { level: 4, name: "Por qué te afecta" })).toBeTruthy();
    expect(screen.getAllByRole("listitem").length).toBeGreaterThanOrEqual(3);
    const link = screen.getByRole("link", { name: /Nota de resultados de NVIDIA/ });
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")).toContain("noopener");
  });

  it("sin estimación todavía, no enseña ninguna cifra", () => {
    render(<NewsCard item={pending as NewsItemOut} />);
    expect(screen.getByText(/Estamos calculando cuánto podría moverla/)).toBeTruthy();
    expect(screen.queryByText(/€/)).toBeNull();
  });

  it("si no afecta a la cartera, lo dice", () => {
    render(<NewsCard item={notRelevant as NewsItemOut} />);
    expect(screen.getByText("No afecta a tu cartera.")).toBeTruthy();
  });
});

describe("textos de la estimación", () => {
  it("plazo en sesiones", () => {
    expect(horizonText(1)).toBe("en la próxima sesión");
    expect(horizonText(5)).toBe("en las próximas 5 sesiones");
  });

  it("de dónde sale el rango", () => {
    const base = NVDA.estimate as NewsEstimateOut;
    expect(methodText({ ...base, method: "volatility", analogs_count: 41 })).toBe(
      "Según cómo se movió en 41 días de noticias fuertes de los últimos tres años",
    );
    expect(methodText({ ...base, method: "measured" })).toMatch(
      /^Medido con los precios de cierre de esa sesión/,
    );
    expect(methodText({ ...base, analogs_count: null })).toBe(
      "Según casos parecidos del histórico",
    );
  });

  it("un rango sin anchura se lee como una sola cifra", () => {
    expect(eurRangeText("-121.40", "-121.20")).toMatch(/^-121\s€$/);
    expect(eurRangeText("-199.00", "-193.00")).toMatch(/^entre -199\s€ y -193\s€$/);
  });

  it("una cifra medida habla en pasado", () => {
    const measured: NewsItemOut = {
      ...NVDA,
      estimate: { ...(NVDA.estimate as NewsEstimateOut), status: "measured", method: "measured" },
    };
    render(<NewsCard item={measured} />);
    expect(screen.getByText(/Ese día tu cartera se movió/)).toBeTruthy();
    expect(screen.getByText("Medido")).toBeTruthy();
  });
});
