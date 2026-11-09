import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { ThemeToggle } from "./ThemeToggle";
import { THEME_STORAGE_KEY, initialTheme } from "./theme";

beforeEach(() => {
  localStorage.clear();
  document.documentElement.dataset.theme = "light";
});
afterEach(cleanup);

describe("ThemeToggle", () => {
  it("es un interruptor con nombre estable", () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole("switch", { name: "Modo oscuro" });
    expect(btn.getAttribute("aria-checked")).toBe("false");
    expect(btn.tagName).toBe("BUTTON");
    expect(btn.getAttribute("type")).toBe("button");
  });

  it("cambia data-theme, aria-checked y guarda la preferencia", () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole("switch", { name: "Modo oscuro" });
    fireEvent.click(btn);
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(btn.getAttribute("aria-checked")).toBe("true");
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");
    fireEvent.click(btn);
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("light");
  });

  it("varios interruptores se mantienen sincronizados", () => {
    render(
      <>
        <ThemeToggle />
        <ThemeToggle showLabel />
      </>,
    );
    const [a, b] = screen.getAllByRole("switch", { name: "Modo oscuro" });
    fireEvent.click(a!);
    expect(b!.getAttribute("aria-checked")).toBe("true");
  });

  it("la preferencia guardada manda sobre la del sistema", () => {
    localStorage.setItem(THEME_STORAGE_KEY, "dark");
    expect(initialTheme()).toBe("dark");
    localStorage.setItem(THEME_STORAGE_KEY, "otro");
    expect(["light", "dark"]).toContain(initialTheme());
  });
});
