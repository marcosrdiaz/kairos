import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render, screen } from "@testing-library/react";
import { TextMorph } from "./TextMorph";

function mockReducedMotion(reduce: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: reduce && query.includes("prefers-reduced-motion"),
    media: query,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
    onchange: null,
  }));
}

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("TextMorph", () => {
  it("con el texto inicial hay un único nodo y sin copia saliente", () => {
    mockReducedMotion(false);
    const { container } = render(<TextMorph text="Todo en orden" />);
    expect(screen.getAllByText("Todo en orden")).toHaveLength(1);
    expect(container.querySelector("[aria-hidden]")).toBeNull();
  });

  it("al cambiar, el texto nuevo está una sola vez y el anterior solo con aria-hidden", () => {
    mockReducedMotion(false);
    vi.useFakeTimers();
    const { container, rerender } = render(<TextMorph text="Todo en orden" />);
    rerender(<TextMorph text="Atento a un evento" />);

    // Durante el fundido: la frase nueva, una vez; la saliente, oculta al lector.
    expect(screen.getAllByText("Atento a un evento")).toHaveLength(1);
    const outgoing = screen.getByText("Todo en orden");
    expect(outgoing.closest("[aria-hidden='true']")).not.toBeNull();
    expect(screen.getByText("Atento a un evento").closest("[aria-hidden]")).toBeNull();

    // El único nodo accesible es el que lleva aria-live.
    expect(container.querySelectorAll("[aria-live='polite']")).toHaveLength(1);
    expect(screen.getByText("Atento a un evento").closest("[aria-live='polite']")).not.toBeNull();

    // Al acabar, la saliente sale del DOM y la nueva sigue una sola vez.
    act(() => {
      vi.advanceTimersByTime(400);
    });
    expect(screen.queryByText("Todo en orden")).toBeNull();
    expect(screen.getAllByText("Atento a un evento")).toHaveLength(1);
    expect(container.querySelector("[aria-hidden]")).toBeNull();
  });

  it("sin cambio de texto no se crea ninguna copia saliente", () => {
    mockReducedMotion(false);
    const { container, rerender } = render(<TextMorph text="Todo en orden" />);
    rerender(<TextMorph text="Todo en orden" />);
    expect(container.querySelector("[aria-hidden]")).toBeNull();
    expect(screen.getAllByText("Todo en orden")).toHaveLength(1);
  });

  it("con prefers-reduced-motion el cambio es instantáneo, sin copia saliente", () => {
    mockReducedMotion(true);
    const { container, rerender } = render(<TextMorph text="Todo en orden" />);
    rerender(<TextMorph text="Atento a un evento" />);
    expect(screen.queryByText("Todo en orden")).toBeNull();
    expect(screen.getAllByText("Atento a un evento")).toHaveLength(1);
    expect(container.querySelector("[aria-hidden]")).toBeNull();
  });

  it("dos cambios seguidos no dejan más de una copia saliente", () => {
    mockReducedMotion(false);
    vi.useFakeTimers();
    const { container, rerender } = render(<TextMorph text="Uno" />);
    rerender(<TextMorph text="Dos" />);
    rerender(<TextMorph text="Tres" />);
    expect(container.querySelectorAll("[aria-hidden='true']")).toHaveLength(1);
    expect(screen.getAllByText("Tres")).toHaveLength(1);
    act(() => {
      vi.advanceTimersByTime(400);
    });
    expect(container.querySelector("[aria-hidden]")).toBeNull();
  });
});
