/**
 * Emisor de un activo para el distintivo del ticker (T2-28). Todo local: un mapa pequeño por
 * nombre, sin logos de terceros ni peticiones externas. Un emisor desconocido no rompe nada:
 * sale con una pastilla neutra y la primera letra del nombre.
 */
export interface Issuer {
  /** Clave del color fijo del grupo (`data-issuer` en el CSS); `neutral` si no se conoce. */
  key: string;
  initials: string;
}

const KNOWN: ReadonlyArray<{ match: RegExp; issuer: Issuer }> = [
  { match: /vanguard/i, issuer: { key: "vanguard", initials: "VG" } },
  { match: /ishares|blackrock/i, issuer: { key: "ishares", initials: "iS" } },
  { match: /apple/i, issuer: { key: "apple", initials: "AP" } },
  { match: /nvidia/i, issuer: { key: "nvidia", initials: "NV" } },
  { match: /microsoft/i, issuer: { key: "microsoft", initials: "MS" } },
  { match: /inditex/i, issuer: { key: "inditex", initials: "IN" } },
  { match: /iberdrola/i, issuer: { key: "iberdrola", initials: "IB" } },
];

export function issuerOf(name: string): Issuer {
  const known = KNOWN.find((k) => k.match.test(name));
  if (known) return known.issuer;
  const first = name.trim().charAt(0).toUpperCase();
  return { key: "neutral", initials: first || "·" };
}
