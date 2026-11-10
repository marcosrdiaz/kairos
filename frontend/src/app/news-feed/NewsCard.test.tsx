import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import type { NewsEstimateOut, NewsItemOut } from "../../api/generated/schema";
import estimated from "../../api/mocks/NewsItemOut.json";
import notRelevant from "../../api/mocks/NewsItemOut.not_relevant.json";
import pending from "../../api/mocks/NewsItemOut.pending.json";
import { NewsCard } from "./NewsCard";
import { horizonText, methodText } from "./labels";

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
    expect(screen.getByText(/Se nota en la sesión · desde el 20 de noviembre de 2026/)).toBeTruthy();
    expect(
      screen.getByText(/Se nota con el siguiente valor liquidativo · desde el 21 de noviembre/),
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
    expect(methodText({ ...base, method: "volatility" })).toMatch(/volatilidad histórica/);
    expect(methodText({ ...base, method: "measured" })).toBe("Medido con los precios de cierre");
    expect(methodText({ ...base, analogs_count: null })).toBe(
      "Según casos parecidos del histórico",
    );
  });
});
