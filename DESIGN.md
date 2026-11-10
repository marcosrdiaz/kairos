---
name: KAIROS
description: El mundo, traducido a tu cartera. Interfaz cálida en oro y papel (o en oro sobre negro), que habla en euros y nunca alarma.
colors:
  primary: "#765600"
  primary-dark-mode: "#f2c14e"
  on-primary: "#ffffff"
  primary-tint: "#f7edd5"
  gold: "#f2c14e"
  bg: "#f5f3ee"
  surface: "#ffffff"
  surface-muted: "#fbf8f2"
  border: "#e6e0d4"
  border-strong: "#857b6b"
  text: "#1d1a15"
  text-muted: "#5a5246"
  bg-dark: "#11100e"
  surface-dark: "#1b1916"
  text-dark: "#f4efe6"
  tranquilo: "#145c33"
  tranquilo-bg: "#e2f2e8"
  atento: "#6e4700"
  atento-bg: "#fcefcf"
  revisa-plan: "#4f2fa8"
  revisa-plan-bg: "#ede8fb"
  error: "#962018"
  error-bg: "#fbe4e2"
  info: "#1647a8"
  info-bg: "#e5eefc"
typography:
  hero:
    fontFamily: "Figtree, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "2.75rem"
    fontWeight: 600
    lineHeight: 1.1
  headline:
    fontFamily: "Figtree, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 600
    lineHeight: 1.2
  title:
    fontFamily: "Figtree, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.25
  body:
    fontFamily: "Figtree, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Figtree, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.4
rounded:
  card: "16px"
  control: "12px"
  pill: "999px"
spacing:
  touch: "44px"
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  nav-item:
    textColor: "{colors.text-muted}"
    typography: "{typography.label}"
    height: "44px"
  nav-item-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.pill}"
    height: "44px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: "20px"
  status-tranquilo:
    backgroundColor: "{colors.tranquilo-bg}"
    textColor: "{colors.tranquilo}"
  status-atento:
    backgroundColor: "{colors.atento-bg}"
    textColor: "{colors.atento}"
  status-revisa-plan:
    backgroundColor: "{colors.revisa-plan-bg}"
    textColor: "{colors.revisa-plan}"
---

# Design System: KAIROS

## Overview

**Creative North Star: "Oro en calma"**

KAIROS es un sitio cálido y ordenado donde alguien de confianza te dice cómo está tu dinero hoy y si tienes que hacer algo. Papel crema y tinta oscura en modo claro; negro cálido y oro en modo oscuro. Mucho aire, tarjetas limpias, una frase grande y pocas cifras. El oro es la marca y la acción principal; el color de estado solo aparece para decir en qué estado estás, siempre junto a una palabra.

La densidad es baja en el móvil (la superficie que usan Laura y Javier) y algo mayor en escritorio. La interfaz nunca grita: los estados del mercado no usan rojo, no hay destellos ni urgencia gratuita. El silencio también es información.

El texto es grande por defecto (18 px de base) porque una parte de los usuarios son mayores y escuchan antes de leer; la voz y su transcripción son ciudadanas de primera, no accesorios.

**Key Characteristics:**
- Dos modos, claro y oscuro, con los mismos tokens (`--kairos-color-*`).
- Oro como acento único de interfaz; el color de estado es un lenguaje, no un adorno.
- Planos: capas tonales y bordes finos, sin sombras.
- Texto base de 18 px, objetivos táctiles de 44 px o más.
- Cada estado lleva color y palabra; nunca solo color.
- Todo par de color pasa WCAG AA, comprobado por test.

## Colors

Los tokens viven en `frontend/src/styles/tokens.css` con el prefijo `--kairos-color-`: modo claro en `:root`, modo oscuro en `[data-theme="dark"]`, con los mismos nombres. Tailwind los expone con los nombres de siempre (`bg-paper`, `bg-surface`, `text-ink`, `text-ink-muted`, `border-line`, `text-accent`, `bg-accent-tint`…) mediante `@theme inline` en `src/index.css`, así que las pantallas no saben en qué modo están.

### Marca
- **Logo** (`LogoMark` / `LogoTile` en `src/components/icons.tsx`): dos barras crecientes y una K cuyo trazo vertical es la tercera barra, con un degradado de `gold` a `gold-deep`. Siempre dentro de su cuadrado redondeado (`LogoTile`, fondo `bg`: crema en claro, negro en oscuro), para que la K no se confunda con el nombre "Kairos" que va al lado.
- **Oro Viejo** (`primary`, #765600 en claro) y **Oro Miel** (#f2c14e en oscuro): elemento activo de la navegación, botón principal, enlaces y anillo de foco. Menos del 10 % de la pantalla.
- **Tinte de oro** (`primary-tint`): fondo de la cabecera de Inicio, iconos de atajo y pestaña activa en móvil.
- **Oro** (`gold`, #f2c14e): solo decorativo (ilustraciones, degradados). Nunca para texto sobre claro.

### Estados del widget (sin rojo)
- *Tranquilo*: verde (`state-tranquilo-fg` sobre `state-tranquilo-bg`).
- *Atento*: ámbar (`state-atento-*`).
- *Revisa tu plan*: violeta (`state-revisa-plan-*`), precisamente para no alarmar.
- Cada estado tiene además un tono `-solid` para franjas decorativas (≥ 3:1 sobre la superficie).

### Chips de sistema
`chip-success`, `chip-warn`, `chip-error`, `chip-info` y `chip-nodata`, cada uno con `-bg` y `-fg`. **El rojo (`chip-error`) es solo para errores del sistema o de formularios** (p. ej. un traspaso no permitido); nunca para el estado del mercado ni para una caída.

### Resto
- Superficies: `bg`, `surface`, `surface-muted`; texto: `text`, `text-muted`; bordes: `border` (decorativo) y `border-strong` (controles).
- Variación: `trend-up` y `trend-down`, siempre con flecha y signo.
- Pérdida en la gráfica de evolución (T2-18): `trend-loss`, naranja (no rojo), con flecha y signo. Solo en esa gráfica y su tabla; el resto de la app sigue con `trend-down`.
- Iconos de tarjeta: `icon-{gold,green,purple,blue,red}-{bg,fg}`. El rojo de icono es decorativo (tarjeta "Valor total"); no comunica estado.
- Gráficos: `chart-1` a `chart-4` (oro, verde azulado, violeta, azul).

### Contraste (WCAG 2.2 AA)
`frontend/src/styles/contrast.test.ts` lee `tokens.css` y exige ≥ 4,5:1 a todo par de texto y ≥ 3:1 a bordes de control, foco, iconos y marcas de gráfico, en los dos modos. Si cambias un color, el test te dice si rompe el contraste. Pares clave:

| Par | Claro | Oscuro |
| --- | --- | --- |
| Texto / fondo | 15,6:1 | 16,6:1 |
| Texto secundario / superficie | 7,7:1 | 8,1:1 |
| Oro (enlace) / superficie | 6,8:1 | 10,5:1 |
| Texto del botón / botón principal | 6,8:1 | 10,3:1 |
| Tranquilo | 6,9:1 | 8,6:1 |
| Atento | 7,2:1 | 8,7:1 |
| Revisa tu plan | 7,6:1 | 8,2:1 |
| Error | 6,9:1 | 8,3:1 |
| Información | 7,2:1 | 8,3:1 |
| Borde de control / superficie | 4,2:1 | 4,3:1 |
| Foco / fondo | 6,1:1 | 11,3:1 |

### Named Rules
**The Palabra Con Color Rule.** Un estado se comunica siempre con color y palabra ("Tranquilo", "Atento", "Revisa tu plan"). El color solo nunca basta.
**The Sin Rojo En El Mercado Rule.** El rojo no se usa para estados, caídas ni impactos; solo para errores del sistema.
**The One Accent Rule.** El oro ocupa menos del 10 % de la pantalla; su escasez es lo que lo hace legible.

## Modo claro y oscuro

- El tema está en `<html data-theme="light|dark">`. Un script en línea de `frontend/index.html` lo fija antes de pintar (sin parpadeo): preferencia guardada en `localStorage` (`kairos-theme`) y, si no hay, la del sistema (`prefers-color-scheme`).
- `src/theme/ThemeToggle.tsx` es un `<button role="switch" aria-checked>` con nombre fijo "Modo oscuro". Al cambiar de modo se cortan las transiciones un instante (clase `theme-switching`) para que todo cambie a la vez; solo el propio interruptor se anima. En escritorio va al pie de la barra lateral con texto e interruptor visual; en móvil, solo icono en la cabecera.
- `color-scheme` cambia con el modo, así que los controles nativos y las barras de desplazamiento siguen el tema.

## Typography

**Familia:** `Figtree` si está instalada y, si no, la pila del sistema (`ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto…`). No se cargan fuentes remotas: la demo debe funcionar sin red.

### Hierarchy
- **Hero** (600, 2.75rem / 44 px, 1.1): cifra de portada.
- **Headline** (600, 2.25rem / 36 px en escritorio, 2rem en móvil, 1.2): la frase de estado en Inicio.
- **Title** (600, 1.5rem / 24 px, 1.25): títulos de sección y valores de tarjeta.
- **Body** (400, 1.125rem / 18 px, 1.5): texto corrido. Líneas de 65 caracteres como máximo.
- **Label** (500, 1rem / 16 px, 1.4): navegación, botones y etiquetas. Nunca por debajo de 16 px.

**The 18 Rule.** Nada de texto legible por debajo de 16 px, y el cuerpo parte de 18 px. Las cifras usan números tabulares.

## Layout

Móvil primero, pero la app también se usa en escritorio.

- **Móvil (< 1024 px):** cabecera fija de 64 px con la marca y el botón de modo oscuro; contenido en una columna de 36 rem (576 px) con 16 px de margen; barra inferior fija con tres pestañas (icono + texto; la activa con una píldora de tinte de oro detrás del icono).
- **Escritorio (≥ 1024 px, `lg`):** barra lateral de 19 rem. Arriba, a sangre, el banner de marca (`BrandBanner`: logo en su cuadrado, "Kairos" y el lema "Analiza · comprende · decide" sobre ondas doradas). Debajo, las secciones (la activa rellena de oro), un separador, el enlace al panel y, al pie, el interruptor de modo oscuro. El contenido ocupa todo el ancho restante con 40 px de margen (56 px en pantallas muy anchas).
- Es un único `<nav aria-label="Secciones">`, recolocado con CSS. Los landmarks (`header`, `nav`, `main`) permiten saltar de zona con el lector de pantalla.
- `scroll-padding` evita que la cabecera o la barra fijas tapen el elemento con foco.
- **Inicio:** cabecera con degradado de tinte de oro (estado, frase como titular, botón "Ver por qué" y, a la derecha, la ilustración `HeroArt`: un globo con una órbita de eventos que desemboca en una moneda en euros, con los colores de los tokens; en oscuro añade estrellas y halo), cuatro tarjetas de cifras (2 columnas en móvil, 4 en escritorio ancho) y una tarjeta de atajos. Previsto: ticker de mercado y gráfica interactiva entre la cabecera y las tarjetas (T2-17, T2-18) y carrusel de noticias debajo de las tarjetas (T2-19).
- El panel (`/panel`) mantiene su layout de escritorio propio.
- El widget de la pantalla de inicio del móvil es un componente aparte que se hará después.

Ritmo de espacio en pasos de 8, 16 y 24 px. Todo objetivo táctil mide al menos 44×44 px. El texto debe poder ampliarse al 200 % sin perder contenido ni producir desplazamiento horizontal.

## Elevation & Depth

Sistema plano de capas tonales: `bg` → `surface-muted` → `surface`, reforzado con un borde de 1 px. Sin sombras. El foco se resuelve con un anillo de 3 px del color de foco.

## Shapes

Tarjetas de 16 px de radio; controles y elementos de navegación de 12 px; botones e insignias en píldora. Iconos de tarjeta en cuadrados de 44 px con radio de 12 px.

## Components

### Navegación
- Elemento: icono + texto, 44 px de alto mínimo. `aria-current="page"` en el activo (lo pone `NavLink`).
- Activo: en escritorio, fondo oro y texto `on-primary`; en móvil, texto oro y píldora de tinte detrás del icono (forma + color).

### Botones (`src/components/button.ts`)
- **Principal:** píldora oro con texto `on-primary`; hover más oscuro (claro) o más claro (oscuro).
- **Secundario:** píldora con borde firme sobre la superficie.
- **Deshabilitado:** gris sin datos; se marca además con `disabled` o `aria-disabled`.

### Tarjetas de cifra (`StatusTiles`)
Una `<dl>`: cada tarjeta es una pareja `<dt>`/`<dd>`, así el lector anuncia "Valor total: 34.311,68 €". El icono es decorativo.

### Insignia de estado
Fondo del estado claro, texto del estado oscuro, punto decorativo y palabra siempre visible. El cambio por polling se anuncia con `aria-live="polite"`.

### Iconos (`src/components/icons.tsx`)
SVG en línea con `currentColor`, `aria-hidden="true"` y `focusable="false"`. El significado siempre lo da el texto.

## Do's and Don'ts

### Do:
- **Do** usar los tokens `--kairos-color-*` (o sus clases de Tailwind); nunca colores sueltos. Un color nuevo se añade en los dos modos y pasa el test de contraste.
- **Do** usar siempre color y palabra para un estado.
- **Do** dar a todo objetivo táctil 44×44 px como mínimo.
- **Do** usar HTML semántico: `<button>` para acciones, `<a>`/`Link` para navegar, `<dl>` para pares etiqueta/valor, encabezados en orden.
- **Do** respetar `prefers-reduced-motion` y `forced-colors`.
- **Do** formatear cifras solo con `src/lib/format.ts`.

### Don't:
- **Don't** usar rojo para el mercado, parpadeos ni iconos de alarma.
- **Don't** transmitir significado solo con el color.
- **Don't** añadir sombras: la profundidad es tonal.
- **Don't** usar fuentes remotas ni librerías de iconos o de componentes sin una decisión.
- **Don't** dibujar gráficos con datos inventados: las ilustraciones decorativas no llevan ejes ni valores.
- **Don't** usar texto por debajo de 16 px.
