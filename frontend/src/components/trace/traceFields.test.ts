import { describe, expect, it } from "vitest";
import { formatDate, formatEur, formatPercent } from "../../lib/format";
import { toTraceFields } from "./traceFields";

describe("toTraceFields", () => {
  it("da formato según la clave y nombra en español", () => {
    expect(toTraceFields({ total_eur: "34311.68", coverage_pct: "0.94", units: "114.00000000" })).toEqual([
      { key: "total_eur", label: "Valor total", text: formatEur("34311.68") },
      { key: "coverage_pct", label: "Cobertura", text: formatPercent("0.94") },
      { key: "units", label: "Participaciones", text: "114" },
    ]);
  });

  it("no pierde precisión con importes grandes", () => {
    const [field] = toTraceFields({ total_eur: "123456789012345.67" });
    expect(field).toMatchObject({ text: formatEur("123456789012345.67") });
    expect(field).toMatchObject({ text: expect.stringContaining("67") });
  });

  it("los hijos sin unidad heredan la del padre", () => {
    expect(toTraceFields({ value_eur: { IE00B4L5Y983: "10.50" } })).toEqual([
      {
        key: "value_eur",
        label: "Valor",
        fields: [{ key: "IE00B4L5Y983", label: "IE00B4L5Y983", text: formatEur("10.50") }],
      },
    ]);
  });

  it("nombra los elementos de una lista por su activo", () => {
    const [field] = toTraceFields({ positions: [{ asset_id: "NVDA", value_eur: "1.00" }] });
    expect(field).toMatchObject({
      label: "Posiciones",
      fields: [{ label: "NVDA", fields: [{ text: "NVDA" }, { text: formatEur("1.00") }] }],
    });
  });

  it("numera los elementos sin nombre", () => {
    const [field] = toTraceFields({ lots: [{ units: "1" }, { units: "2" }] });
    expect(field).toMatchObject({ fields: [{ label: "1" }, { label: "2" }] });
  });

  it("muestra nulos, vacíos, booleanos y fechas", () => {
    expect(toTraceFields({ a: null, b: [], c: {}, on_track: true, end: "2026-11-08T18:00:00Z" })).toEqual([
      { key: "a", label: "a", text: "—" },
      { key: "b", label: "b", text: "—" },
      { key: "c", label: "c", text: "—" },
      { key: "on_track", label: "En camino", text: "Sí" },
      { key: "end", label: "Fin", text: formatDate("2026-11-08T18:00:00Z") },
    ]);
  });

  it("un texto no numérico se queda igual aunque la clave tenga unidad", () => {
    expect(toTraceFields({ value_eur: "n/d" })).toMatchObject([{ text: "n/d" }]);
  });

  it("une las listas de valores simples", () => {
    expect(toTraceFields({ events: ["bce", "nvda"] })).toMatchObject([{ text: "bce, nvda" }]);
  });

  it("traduce los valores de enumeraciones conocidos y deja el resto igual", () => {
    expect(
      toTraceFields({ event_type: "central_bank", surprise: { label: "en_linea" }, title: "en_linea" }),
    ).toMatchObject([
      { text: "Banco central" },
      { fields: [{ label: "Descripción", text: "En línea con lo esperado" }] },
      { text: "en_linea" },
    ]);
  });

  it("nombra los elementos de una lista por su nombre antes que por el ISIN", () => {
    const [field] = toTraceFields({ breakdown: [{ asset_id: "IE00B4L5Y983", name: "iShares Core MSCI World" }] });
    expect(field).toMatchObject({ label: "Desglose por activo", fields: [{ label: "iShares Core MSCI World" }] });
  });

  it("muestra caídas y rentabilidades como porcentaje", () => {
    expect(toTraceFields({ drop: "-0.04", annual_return: "0.0375" })).toEqual([
      { key: "drop", label: "Caída", text: formatPercent("-0.04") },
      { key: "annual_return", label: "Rentabilidad anual", text: formatPercent("0.0375") },
    ]);
  });

  it("da nombre a todas las claves que escribe hoy el backend en las trazas", () => {
    // Claves de `calc_trace` tras el guion de demo completo (9 tipos de traza), sin ISIN ni ids.
    const keys = [
      "EQ_GLOBAL", "EQ_US_TECH", "EURUSD", "OIL", "RATES_EUR", "acquired_at", "actual",
      "adjustment_eur", "allocation", "amount_eur", "annual_return", "as_of", "asset_id",
      "asset_name", "base", "beta", "betas", "breakdown", "by_asset", "by_country", "by_currency",
      "by_sector", "cash", "causal_chain", "change_eur", "change_pct", "change_week_eur",
      "change_week_pct", "channel", "company_moves", "company_weights", "confidence",
      "cost_eur_per_unit", "coverage_pct", "currency", "current", "current_value_eur", "dca_plans",
      "demo_adjustments", "detail", "drift_equity", "drift_exceeded", "drift_threshold", "drop",
      "end", "end_value_eur", "equity", "equity_current", "equity_target", "event_id",
      "event_impact_eur", "event_type", "events", "expected", "explanation", "explanation_status",
      "factor_shocks", "fixed_income", "flows_eur", "frequency", "fx_eur", "fx_rate", "gap_eur",
      "goal_amount_eur", "goal_year", "high_eur", "id", "impact_eur", "impact_pct", "items", "key",
      "kind", "label", "lots", "low_eur", "market_eur", "metric", "mixed",
      "monthly_contribution_eur", "months", "n", "n_rows", "name", "net_flows_eur", "num_holdings",
      "occurred_at", "on_track", "optimista", "period", "pesimista", "polarity", "portfolio_id",
      "positions", "price", "price_at", "price_kind", "quotes", "r2", "r2_weighted", "radiography",
      "reaches_goal", "reason_kind", "ref", "returns_by_class", "rule", "scenarios", "selected_by",
      "single_fired", "sources", "start", "start_value_eur", "state", "status", "std_err",
      "surprise", "target", "title", "top10_fired", "top10_weight", "top_companies_group",
      "top_country", "top_currency", "top_currency_weight", "top_name", "top_weight", "total_eur",
      "unexplained_eur", "unit_eur_end", "unit_eur_start", "units", "units_end", "units_start",
      "url", "value_at_goal_eur", "value_change", "value_eur", "value_eur_by_class",
      "week_ago_unit_eur", "weight",
    ];
    const unnamed = toTraceFields(Object.fromEntries(keys.map((k) => [k, "x"])))
      .filter((field) => field.label === field.key)
      .map((field) => field.key);
    expect(unnamed).toEqual([]);
  });
});
