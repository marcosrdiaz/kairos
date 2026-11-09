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
  it("es un botón de alternancia con nombre estable", () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole("button", { name: "Modo oscuro" });
    expect(btn.getAttribute("aria-pressed")).toBe("false");
    expect(btn.getAttribute("type")).toBe("button");
  });

  it("cambia data-theme, aria-pressed y guarda la preferencia", () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole("button", { name: "Modo oscuro" });
    fireEvent.click(btn);
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(btn.getAttribute("aria-pressed")).toBe("true");
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
    const [a, b] = screen.getAllByRole("button", { name: "Modo oscuro" });
    fireEvent.click(a!);
    expect(b!.getAttribute("aria-pressed")).toBe("true");
  });

  it("la preferencia guardada manda sobre la del sistema", () => {
    localStorage.setItem(THEME_STORAGE_KEY, "dark");
    expect(initialTheme()).toBe("dark");
    localStorage.setItem(THEME_STORAGE_KEY, "otro");
    expect(["light", "dark"]).toContain(initialTheme());
  });
});
