/** «Laura» → «L»; «Familia García» → «FG». */
export function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  return words
    .slice(0, 2)
    .map((w) => w.charAt(0).toLocaleUpperCase("es"))
    .join("");
}
