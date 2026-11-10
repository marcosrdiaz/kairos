### D-XXX · Laboratorio de componentes (`/lab`) y dependencias de la fase 5 (T5-01)
- Fecha: 2026-11-10 · Autor: Marcos · Estado: Propuesta
- Contexto: el equipo quiere ver en la web varios componentes de librerías externas (Bklit UI, Kokonut UI, Cult UI, Componentry y React Bits) antes de decidir cuáles aplicar en la fase 5. DESIGN.md pide no añadir librerías de componentes sin una decisión.
- Decisión:
  - **Laboratorio solo de desarrollo.** La ruta `/lab` se monta únicamente si `import.meta.env.DEV` y se carga con `lazy()`: no entra en el build ni en el bundle principal. No toca ninguna pantalla real. Todos los datos son ilustrativos (`frontend/src/lab/mock.ts`).
  - **Código copiado y adaptado a mano** en `frontend/src/ui/`, con imports relativos y `cn()` en `src/lib/cn.ts`. No se inicializa shadcn ni se tocan `tsconfig.json` ni `vite.config.ts`. Cada fichero lleva en su cabecera el origen, la licencia y los cambios.
  - **Dependencias nuevas** (versión exacta): `motion` 14.12.0, `d3-shape` 3.2.1, `d3-scale` 4.0.3, `clsx` 2.1.1 y `tailwind-merge` 3.7.0; y, de desarrollo, `@types/d3-shape` 3.2.0 y `@types/d3-scale` 4.0.9. `d3-shape` y `d3-scale` ya viajaban en el bundle a través de Recharts.
  - **Licencias comprobadas en GitHub (`LICENSE`):** Bklit UI (`bklit/bklit-ui`) MIT · Kokonut UI (`KokonutUI/kokonutui`) MIT · Cult UI (`nolly-studio/cult-ui`) MIT · Componentry (`harshjdhv/componentry`) MIT. **React Bits (`DavidHDev/react-bits`) es «MIT + Commons Clause»**: permite usarlo en una aplicación pero prohíbe redistribuir los componentes, así que no se considera equivalente a MIT y **no se copia nada de él**. «Spotlight Card» es una implementación propia de la misma idea, y en lugar de Count Up se usa Rolling Number de Cult UI.
  - **Origen de cada componente de `src/ui/`:**

    | Componente | Origen | Qué se conserva |
    | --- | --- | --- |
    | `Sparkline`, `sparkline-geometry` | Bklit UI, Sparkline (MIT) | Geometría (dominio, layout, rutas de línea y área); se quitan barras e interpolaciones |
    | `RangeBandChart`, `band-geometry` | Bklit UI, Band (MIT) | La idea y la forma del área entre bordes; render propio, sin morphing |
    | `MetricCard` | Kokonut UI, Metric Card (MIT) | Estructura (cifra, periodos, comparación); reescrita con los tokens |
    | `UptimeCard` | Kokonut UI, Uptime Card (MIT) | Filas de barras diarias; sin física ni rojo |
    | `SwipeTabs` | Kokonut UI, Swipe Tabs (MIT) | Indicador deslizante y deslizamiento del panel; reescrita |
    | `PipelineSteps` | Kokonut UI, Currency Transfer (MIT) | Solo la línea de pasos |
    | `ProgressBar` | Cult UI, Halo Progress (MIT) | Relleno con `scaleX` y muelle; sin brillo, cristal ni Base UI |
    | `RollingNumber` | Cult UI, Rolling Number (MIT) | Muelle + `useTransform`; sobreamortiguado |
    | `TextMorph` | Componentry, Text Morph (MIT) | Fundido con desenfoque, sin rotación automática |
    | `GrainGradient` | Componentry, Grain Gradient (MIT) | Shader, dibujado una sola vez |
    | `SpotlightCard` | Propia (idea de React Bits) | — |

  - Los originales superaban de largo las 300 líneas por fichero del proyecto (Kokonut: 560–870 líneas cada uno) y traían iconos de `lucide-react`, colores propios y textos de demostración, así que se adaptan en lugar de copiarse tal cual.
  - **Veredicto frente a DESIGN.md** (visible en cada sección del lab): encajan la banda de rango, los sparklines, la tarjeta de cifra, el estado de fuentes, la barra de progreso, las pestañas, los pasos y el cambio de frase. **Chocan**: la tarjeta con foco de luz (decoración sin información, solo con ratón), el fondo con grano (ruido sobre una cabecera que ya tiene degradado e ilustración, y un contexto WebGL más) y el número que rueda («calma, nunca alarma»: recuerda a una cotización en directo).
- Motivo: poder compararlos en la web, con los tokens de KAIROS en claro y oscuro y `prefers-reduced-motion`, sin comprometer ninguna pantalla ni el peso del build.
- Alternativas descartadas: inicializar shadcn (obliga a tocar `tsconfig.json` y `vite.config.ts`, ficheros compartidos); aplicar los componentes directamente en las pantallas (choca con T4-13 y T3-02 y no deja comparar); copiar React Bits (licencia con cláusula Commons Clause).
- Consecuencias:
  - Tailwind escanea `src/ui` y `src/lab`. `@source not "./lab";` en `src/index.css` deja fuera las clases del lab, pero las de `src/ui` siguen entrando en el CSS del build: +3,2 kB (+0,45 kB gzip) sobre el CSS de partida. Es el coste de tener los componentes en el repo sin usar; desaparece al borrar los descartados y se vuelve uso real al aplicar los elegidos.
  - Quien aplique un componente en una pantalla real (T5-02 en adelante) lo envuelve con `Traced` y formatea con `lib/format.ts`: los componentes no calculan cifras.
  - Si el equipo descarta un componente, se borra su fichero de `src/ui/` y su sección de `src/lab/`.
