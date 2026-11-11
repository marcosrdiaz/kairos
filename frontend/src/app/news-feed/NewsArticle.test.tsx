import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { NewsEstimateOut, NewsItemOut } from "../../api/generated/schema";
import estimated from "../../api/mocks/NewsItemOut.json";
import notRelevant from "../../api/mocks/NewsItemOut.not_relevant.json";
import pending from "../../api/mocks/NewsItemOut.pending.json";
import { NewsArticle } from "./NewsArticle";
import { eurRangeText, horizonText, methodText, sessionsText } from "./labels";

afterEach(cleanup);

const NVDA = estimated as NewsItemOut;

describe("NewsArticle", () => {
  it("empieza por el efecto en la cartera: rango, plazo, tipo de cifra y confianza", () => {
    render(<NewsArticle item={NVDA} />);
    const article = screen.getByRole("article", { name: NVDA.title });
    const effect = article.querySelector("p.text-lg");
    expect(effect?.textContent).toMatch(
      /Tu cartera podría moverse entre -270\s€ y -110\s€ en las próximas 5 sesiones\./,
    );
    expect(screen.getByText("Estimado")).toBeTruthy();
    expect(screen.getByText("Confianza media")).toBeTruthy();
    expect(screen.getByText(/entre -0,6\s% y -0,3\s%/)).toBeTruthy();
    expect(screen.getByText(/Según 8 casos parecidos del histórico/)).toBeTruthy();
    expect(article.querySelector("svg[data-news-art]")).not.toBeNull();
    expect(article.querySelector("[data-news-value-tone='riesgo']")?.className).toContain(
      "text-trend-down",
    );
    // La cifra lleva su calc_id para «¿De dónde sale?».
    expect(article.querySelector(`[data-calc-id="${NVDA.estimate!.calc_id}"]`)).not.toBeNull();
  });

  it("dice desde cuándo se nota en cada posición", () => {
    render(<NewsArticle item={NVDA} />);
    expect(screen.getByText(/Se nota en la sesión · desde el 27 de febrero de 2025/)).toBeTruthy();
    expect(
      screen.getByText(/Se nota con el siguiente valor liquidativo · desde el 28 de febrero/),
    ).toBeTruthy();
  });

  it("enseña por qué afecta y enlaza la fuente en otra pestaña", () => {
    render(<NewsArticle item={NVDA} />);
    expect(screen.getByRole("heading", { level: 4, name: "Por qué te afecta" })).toBeTruthy();
    expect(screen.getAllByRole("listitem").length).toBeGreaterThanOrEqual(3);
    const link = screen.getByRole("link", { name: /Nota de resultados de NVIDIA/ });
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")).toContain("noopener");
  });

  it("sin estimación todavía, no enseña ninguna cifra", () => {
    render(<NewsArticle item={pending as NewsItemOut} />);
    expect(screen.getByText(/Estamos calculando cuánto podría moverla/)).toBeTruthy();
    expect(screen.queryByText(/€/)).toBeNull();
  });

  it("si no afecta a la cartera, lo dice", () => {
    render(<NewsArticle item={notRelevant as NewsItemOut} />);
    expect(screen.getByText("No afecta a tu cartera.")).toBeTruthy();
  });
});

describe("textos de la estimación", () => {
  it("plazo en sesiones", () => {
    expect(horizonText(1)).toBe("en la próxima sesión");
    expect(horizonText(5)).toBe("en las próximas 5 sesiones");
    expect(sessionsText(1)).toBe("1 sesión");
    expect(sessionsText(5)).toBe("5 sesiones");
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
    render(<NewsArticle item={measured} />);
    expect(screen.getByText(/Ese día tu cartera se movió/)).toBeTruthy();
    expect(screen.getByText("Medido")).toBeTruthy();
  });

  it("usa el color semántico de subida para una oportunidad", () => {
    const opportunity = {
      ...NVDA,
      estimate: {
        ...NVDA.estimate!,
        polarity: "oportunidad",
        low_eur: "110",
        high_eur: "270",
        low_pct: "0.003",
        high_pct: "0.006",
      },
    } as NewsItemOut;
    render(<NewsArticle item={opportunity} />);
    expect(screen.getByText(/entre 110\s€ y 270\s€/).className).toContain("text-trend-up");
    expect(screen.getByText("Estimado").className).toContain("bg-icon-gold-bg");
  });

  it("un texto que no cabe sale recortado con «Mostrar más», y se despliega", () => {
    // jsdom no mide: se simula un texto más alto que su caja.
    const height = vi.spyOn(HTMLElement.prototype, "scrollHeight", "get").mockReturnValue(400);
    try {
      render(<NewsArticle item={NVDA} />);
      const more = screen.getByRole("button", { name: "Mostrar más" });
      expect(more.getAttribute("aria-expanded")).toBe("false");
      expect(screen.getByText(NVDA.summary).className).toMatch(/line-clamp/);
      fireEvent.click(more);
      expect(
        screen.getByRole("button", { name: "Mostrar menos" }).getAttribute("aria-expanded"),
      ).toBe("true");
      expect(screen.getByText(NVDA.summary).className).not.toMatch(/line-clamp/);
    } finally {
      height.mockRestore();
    }
  });

  it("si el texto cabe, no hay «Mostrar más»", () => {
    render(<NewsArticle item={NVDA} />);
    expect(screen.queryByRole("button", { name: "Mostrar más" })).toBeNull();
  });
});
