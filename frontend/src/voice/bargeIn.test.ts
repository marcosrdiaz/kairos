import { describe, expect, it } from "vitest";
import { BARGE_IN, BargeDetector } from "./bargeIn";

const STEP = 40;

/** Alimenta el detector con un volumen constante durante `ms`; devuelve si llegó a cortar. */
function feed(d: BargeDetector, from: number, ms: number, mic: number, playback: number): [boolean, number] {
  let t = from;
  let barge = false;
  for (; t < from + ms; t += STEP) barge = d.update(mic, playback, t) || barge;
  return [barge, t];
}

describe("BargeDetector", () => {
  it("sin respuesta sonando, corta cuando la voz supera el fondo durante holdMs", () => {
    const d = new BargeDetector();
    let [barge, t] = feed(d, 0, 1000, 0.02, 0); // ruido de fondo
    expect(barge).toBe(false);
    [barge, t] = feed(d, t, BARGE_IN.holdMs - STEP, 0.5, 0);
    expect(barge).toBe(false); // aún no ha durado lo bastante
    [barge] = feed(d, t, 2 * STEP, 0.5, 0);
    expect(barge).toBe(true);
  });

  it("un golpe corto no corta", () => {
    const d = new BargeDetector();
    const [barge] = feed(d, 0, 80, 0.8, 0);
    expect(barge).toBe(false);
  });

  it("no se corta sola con el eco de la respuesta, aunque se cuele mucho", () => {
    const d = new BargeDetector();
    const [barge] = feed(d, 0, 4000, 0.45, 0.8); // la mitad de la respuesta vuelve por el micro
    expect(barge).toBe(false);
  });

  it("con eco aprendido, la voz del usuario por encima de la respuesta corta", () => {
    const d = new BargeDetector();
    const [calibrated, t] = feed(d, 0, 3000, 0.08, 0.8); // buena cancelación de eco
    expect(calibrated).toBe(false);
    const [barge] = feed(d, t, 400, 0.5, 0.8); // el usuario habla por encima
    expect(barge).toBe(true);
  });

  it("al empezar a sonar la respuesta solo calibra (warmupMs)", () => {
    const d = new BargeDetector();
    const [barge] = feed(d, 0, BARGE_IN.warmupMs - STEP, 0.9, 0.8);
    expect(barge).toBe(false);
  });
});
