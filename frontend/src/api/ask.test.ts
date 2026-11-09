import { describe, expect, it } from "vitest";
import { parseSse } from "./ask";

const meta = { type: "meta", turn_id: "turn_1", disclaimer: true };
const sentence = { type: "sentence", turn_id: "turn_1", index: 0, text: "Frase.", calc_ids: [] };

describe("parseSse", () => {
  it("separa eventos completos y guarda el resto sin terminar", () => {
    const raw = `data: ${JSON.stringify(meta)}\n\ndata: ${JSON.stringify(sentence).slice(0, 20)}`;
    const { events, rest } = parseSse(raw);
    expect(events).toEqual([meta]);
    expect(rest).toBe(`data: ${JSON.stringify(sentence).slice(0, 20)}`);
  });

  it("une un evento partido entre dos trozos", () => {
    const full = `data: ${JSON.stringify(sentence)}\n\n`;
    const first = parseSse(full.slice(0, 15));
    expect(first.events).toEqual([]);
    expect(parseSse(first.rest + full.slice(15)).events).toEqual([sentence]);
  });

  it("acepta CRLF y líneas que no son data", () => {
    const raw = `: comentario\r\nevent: x\r\ndata: ${JSON.stringify(meta)}\r\n\r\n`;
    expect(parseSse(raw).events).toEqual([meta]);
  });
});
