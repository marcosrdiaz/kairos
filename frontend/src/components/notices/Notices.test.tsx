import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { AppNotice, PanelNotice } from "./Notices";
import { APP_NOTICE, PANEL_NOTICE_LINES, PANEL_NOTICE_TITLE } from "./texts";

afterEach(cleanup);

const ALL_TEXTS = [APP_NOTICE, PANEL_NOTICE_TITLE, ...PANEL_NOTICE_LINES];

describe("avisos de IA y no asesoramiento", () => {
  it("el aviso del panel es una región con título y dice IA y no asesoramiento", () => {
    render(<PanelNotice />);
    const region = screen.getByRole("region", { name: PANEL_NOTICE_TITLE });
    expect(region.textContent).toMatch(/inteligencia artificial/);
    expect(region.textContent).toMatch(/No es asesoramiento financiero/);
    expect(region.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
  });

  it("el pie de la app dice IA y no asesoramiento", () => {
    render(<AppNotice />);
    expect(screen.getByText(APP_NOTICE)).toBeTruthy();
    expect(APP_NOTICE).toMatch(/inteligencia artificial/);
    expect(APP_NOTICE).toMatch(/No es asesoramiento financiero/);
  });

  it("los textos no llevan cifras ni órdenes (reglas 1 y 2 de producto)", () => {
    for (const text of ALL_TEXTS) {
      expect(text).not.toMatch(/\d/);
      expect(text).not.toMatch(/\b(compra|vende|te recomiendo|deberías)\b/i);
    }
  });
});
