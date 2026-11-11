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

describe("placeCard con el botón flotante del chat", () => {
  const FULL: Box = { left: 300, top: 0, right: 1440, bottom: 900 };
  const LAUNCHER: Box = { left: 1324, top: 784, right: 1412, bottom: 872 };

  it("una cifra a 860 px abre por encima aunque esté por debajo del botón", () => {
    const place = placeCard(box(400, 860, 80, 43), { width: 320, height: 180 }, FULL, LAUNCHER);
    expect(place.side).toBe("above");
    expect(place.top).toBe(860 - 8 - 180);
  });

  it("el botón no recorta el sitio de las cifras que no están en su columna", () => {
    const place = placeCard(box(400, 600), { width: 320, height: 180 }, FULL, LAUNCHER);
    expect(place).toMatchObject({ side: "below", top: 632, left: 400 });
  });

  it("se corre a la izquierda del botón si lo tocaría", () => {
    const place = placeCard(box(1300, 800), { width: 320, height: 180 }, FULL, LAUNCHER);
    expect(place.left + place.width).toBeLessThanOrEqual(LAUNCHER.left - 8);
  });

  it("sin sitio a su izquierda, no baja más allá de la parte alta del botón", () => {
    const narrow: Box = { left: 1300, top: 0, right: 1440, bottom: 900 };
    const high: Box = { left: 1324, top: 300, right: 1412, bottom: 400 };
    const place = placeCard(box(1310, 100), { width: 320, height: 300 }, narrow, high);
    expect(place.side).toBe("below");
    expect(place.top + place.maxHeight).toBeLessThanOrEqual(high.top - 8);
  });
});
