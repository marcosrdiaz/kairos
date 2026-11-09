import { describe, expect, it } from "vitest";
import { dateInputToIso, parseDecimalInput } from "./decimalInput";

describe("parseDecimalInput", () => {
  it.each([
    ["114", 8, "114"],
    ["102,80591101", 8, "102.80591101"],
    ["102.80591101", 8, "102.80591101"],
    ["80,27", 2, "80.27"],
    [" 1 234,5 ", 2, "1234.5"],
    ["0,5", 2, "0.5"],
    ["007", 8, "7"],
  ])("%s (%i dec) -> %s", (raw, max, value) => {
    expect(parseDecimalInput(raw, max)).toEqual({ ok: true, value });
  });

  it.each([
    ["", "Escribe una cifra."],
    ["abc", "Escribe solo números, con coma para los decimales."],
    ["-5", "Escribe solo números, con coma para los decimales."],
    ["1e3", "Escribe solo números, con coma para los decimales."],
    ["1.234,56", "Escríbela sin separador de miles, por ejemplo 1234,56."],
    ["1,234.56", "Escríbela sin separador de miles, por ejemplo 1234,56."],
    ["0", "Tiene que ser mayor que cero."],
    ["0,00", "Tiene que ser mayor que cero."],
    ["80,271", "Como mucho 2 decimales (céntimos)."],
  ])("%s -> error", (raw, error) => {
    expect(parseDecimalInput(raw, 2)).toEqual({ ok: false, error });
  });

  it("limita las participaciones a 8 decimales", () => {
    expect(parseDecimalInput("1,123456789", 8)).toEqual({
      ok: false,
      error: "Como mucho 8 decimales.",
    });
  });
});

describe("dateInputToIso", () => {
  it("fija el inicio del día en UTC", () => {
    expect(dateInputToIso("2023-03-06")).toBe("2023-03-06T00:00:00Z");
  });
});
