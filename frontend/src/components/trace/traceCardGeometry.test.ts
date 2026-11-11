import { describe, expect, it } from "vitest";
import { placeCard, type Box } from "./traceCardGeometry";

const BOUNDS: Box = { left: 300, top: 64, right: 1100, bottom: 800 };
const box = (left: number, top: number, width = 80, height = 24): Box => ({
  left,
  top,
  right: left + width,
  bottom: top + height,
});

describe("placeCard", () => {
  it("abre debajo de la cifra, alineada a su borde izquierdo", () => {
    const place = placeCard(box(400, 200), { width: 320, height: 180 }, BOUNDS);
    expect(place).toMatchObject({ side: "below", left: 400, top: 232, width: 320 });
    expect(place.maxHeight).toBe(800 - 224 - 8);
  });

  it("se va arriba si debajo no cabe y arriba hay más sitio", () => {
    const place = placeCard(box(400, 700), { width: 320, height: 180 }, BOUNDS);
    expect(place.side).toBe("above");
    expect(place.top).toBe(700 - 8 - 180);
  });

  it("se queda debajo si no cabe en ninguno de los dos lados pero debajo hay más sitio", () => {
    const place = placeCard(box(400, 150), { width: 320, height: 900 }, BOUNDS);
    expect(place.side).toBe("below");
    expect(place.maxHeight).toBe(800 - 174 - 8);
  });

  it("no se sale por la derecha del contenido (chat abierto)", () => {
    const place = placeCard(box(1050, 200), { width: 320, height: 100 }, BOUNDS);
    expect(place.left).toBe(1100 - 320);
  });

  it("no se sale por la izquierda del contenido (barra lateral)", () => {
    const place = placeCard(box(250, 200), { width: 320, height: 100 }, BOUNDS);
    expect(place.left).toBe(300);
  });

  it("estrecha la tarjeta si el contenido es más estrecho que ella", () => {
    const narrow: Box = { left: 16, top: 64, right: 256, bottom: 700 };
    const place = placeCard(box(40, 200), { width: 320, height: 100 }, narrow);
    expect(place).toMatchObject({ left: 16, width: 240 });
  });
});
