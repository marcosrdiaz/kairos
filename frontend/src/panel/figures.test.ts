import { describe, expect, it } from "vitest";
import { impactRange, signedEur } from "./figures";

describe("impactRange", () => {
  it("rango normal: entre X y Y", () => {
    expect(impactRange("-10.00", "190.00")).toMatch(/^entre -10\s€ y 190\s€$/);
  });
  it("low == high: ≈ importe, no 'entre X y X'", () => {
    expect(impactRange("-223.69", "-223.69")).toMatch(/^≈ -224\s€$/);
    expect(impactRange("0.00", "0.00")).toMatch(/^≈ 0\s€$/);
  });
  it("extremos distintos pero iguales al redondear también colapsan", () => {
    expect(impactRange("-4.80", "-5.20")).toMatch(/^≈ -5\s€$/);
  });
});

describe("signedEur", () => {
  it("signo explícito", () => {
    expect(signedEur("90.00")).toMatch(/^\+90,00\s€$/);
    expect(signedEur("-514.00")).toMatch(/^-514,00\s€$/);
  });
});
