/** Bloques del panel, en el orden en que se pintan. La cabecera enlaza a cada uno por su `id`. */
export const PANEL_SECTIONS = [
  { id: "resumen", label: "Resumen" },
  { id: "eventos", label: "Eventos" },
  { id: "exposicion", label: "Exposición" },
  { id: "radar", label: "Radar" },
  { id: "agenda", label: "Agenda" },
  { id: "escenarios", label: "¿Y si…?" },
] as const;
