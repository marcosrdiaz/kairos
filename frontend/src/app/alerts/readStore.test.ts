import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { markRead, useReadIds } from "./readStore";

beforeEach(() => localStorage.clear());
afterEach(() => vi.restoreAllMocks());

describe("readStore", () => {
  it("guarda los leídos por cartera y avisa a quien escucha", () => {
    const { result } = renderHook(() => useReadIds("laura"));
    expect(result.current.size).toBe(0);
    act(() => markRead("laura", ["a", "b"]));
    expect([...result.current]).toEqual(["a", "b"]);
    act(() => markRead("laura", ["b", "c"]));
    expect([...result.current]).toEqual(["a", "b", "c"]);
    expect(localStorage.getItem("kairos-alerts-read:javier")).toBeNull();
  });

  it("ignora lo guardado si no es una lista de ids", () => {
    localStorage.setItem("kairos-alerts-read:laura", "{roto");
    const { result } = renderHook(() => useReadIds("laura"));
    expect(result.current.size).toBe(0);
  });

  it("con el almacenamiento bloqueado, sigue funcionando en memoria", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("bloqueado", "SecurityError");
    });
    const { result } = renderHook(() => useReadIds("bloqueada"));
    act(() => markRead("bloqueada", ["x"]));
    expect(result.current.has("x")).toBe(true);
  });
});
