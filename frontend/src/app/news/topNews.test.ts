import { describe, expect, it } from "vitest";
import type { NewsItemOut } from "../../api/generated/schema";
import estimated from "../../api/mocks/NewsItemOut.json";
import pending from "../../api/mocks/NewsItemOut.pending.json";
import { topNews } from "./topNews";

const NOW = new Date("2026-11-11T12:00:00Z");

/** Una noticia del ejemplo de contrato con otra fecha y otro impacto. */
function news(id: string, publishedAt: string, impact: string): NewsItemOut {
  const base = estimated as NewsItemOut;
  return {
    ...base,
    id,
    published_at: publishedAt,
    estimate: { ...base.estimate!, impact_eur: impact },
  };
}

describe("topNews", () => {
  it("se queda con las de las últimas 24 horas", () => {
    const items = [
      news("recent", "2026-11-11T09:00:00Z", "-50.00"),
      news("edge", "2026-11-10T12:00:00Z", "-40.00"),
      news("old", "2026-11-10T11:59:00Z", "-900.00"),
      news("future", "2026-11-11T12:01:00Z", "-900.00"),
    ];
    expect(topNews(items, NOW).map((n) => n.id)).toEqual(["recent", "edge"]);
  });

  it("ordena por el tamaño del impacto, suba o baje", () => {
    const items = [
      news("small", "2026-11-11T10:00:00Z", "-20.00"),
      news("up", "2026-11-11T09:00:00Z", "300.00"),
      news("down", "2026-11-11T08:00:00Z", "-120.00"),
    ];
    expect(topNews(items, NOW).map((n) => n.id)).toEqual(["up", "down", "small"]);
  });

  it("a igual impacto, primero la más reciente", () => {
    const items = [
      news("earlier", "2026-11-11T08:00:00Z", "-70.00"),
      news("later", "2026-11-11T10:00:00Z", "70.00"),
    ];
    expect(topNews(items, NOW).map((n) => n.id)).toEqual(["later", "earlier"]);
  });

  it("como mucho 5", () => {
    const items = Array.from({ length: 8 }, (_, i) =>
      news(`n${i}`, "2026-11-11T10:00:00Z", `${(i + 1) * 10}.00`),
    );
    expect(topNews(items, NOW).map((n) => n.id)).toEqual(["n7", "n6", "n5", "n4", "n3"]);
  });

  it("deja fuera las que aún no tienen cifra", () => {
    const calculating = { ...(pending as NewsItemOut), published_at: "2026-11-11T10:00:00Z" };
    const unclassified = { ...news("raw", "2026-11-11T10:00:00Z", "0"), estimate: null };
    expect(topNews([calculating, unclassified], NOW)).toEqual([]);
  });
});
