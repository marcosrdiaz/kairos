---
name: KAIROS
description: El mundo, traducido a tu cartera. Interfaz tranquila, de papel y tinta, que habla en euros y nunca alarma.
colors:
  paper: "#faf8f4"
  surface: "#ffffff"
  ink: "#1b2430"
  ink-muted: "#4a5565"
  line: "#ddd8ce"
  line-strong: "#8a8f98"
  accent: "#2f4b7c"
  on-accent: "#ffffff"
  tranquilo: "#1f5f46"
  tranquilo-bg: "#e3f1ea"
  atento: "#7a4b00"
  atento-bg: "#fbefd2"
  revisa-plan: "#4b3a9a"
  revisa-plan-bg: "#e9e6f8"
typography:
  hero:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "2.75rem"
    fontWeight: 600
    lineHeight: 1.1
  headline:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "2rem"
    fontWeight: 600
    lineHeight: 1.2
  title:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.25
  body:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.4
rounded:
  card: "16px"
spacing:
  touch: "44px"
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  tab:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
    height: "56px"
  tab-active:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.accent}"
  note-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.card}"
    padding: "16px"
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

**Creative North Star: "El Cuaderno Sereno"**

KAIROS se comporta como un cuaderno de papel cálido en el que alguien de confianza ha apuntado una sola cosa: cómo está tu dinero hoy y si tienes que hacer algo. Tinta oscura sobre papel, mucho aire, una cifra y una frase. El color no decora: solo aparece para decir en qué estado estás, y siempre junto a una palabra.

La densidad es baja en el móvil (la superficie que usan Laura y Javier) y algo mayor en el panel de escritorio, donde se profundiza. La interfaz nunca grita: no hay rojos, ni destellos, ni urgencia gratuita. El silencio también es información.

El texto es grande por defecto (18 px de base) porque una parte de los usuarios son mayores y escuchan antes de leer; la voz y su transcripción son ciudadanas de primera, no accesorios.

**Key Characteristics:**
- Papel cálido y tinta oscura; el color es un lenguaje de estado, no un adorno.
- Planos y táctiles: capas tonales y bordes finos, sin sombras.
- Texto base de 18 px, objetivos táctiles de 44 px o más.
- Cada estado lleva color y palabra; nunca solo color.
- Sin rojos ni urgencia visual.

## Colors

Paleta de papel y tinta con un azul sobrio como único acento y tres colores de estado apagados.

### Primary
- **Azul Tinta de Pluma** (#2f4b7c): pestaña activa, enlaces, anillo de foco y marca. Es el único acento de interfaz; se usa en menos del 10 % de cualquier pantalla.

### Secondary (estados del widget)
- **Verde Pino** (#1f5f46) sobre **Verde Bruma** (#e3f1ea): estado *Tranquilo*. Ratio 6,5:1.
- **Ámbar Tostado** (#7a4b00) sobre **Miel Pálida** (#fbefd2): estado *Atento*. Ratio 6,5:1.
- **Índigo Ciruela** (#4b3a9a) sobre **Lavanda Bruma** (#e9e6f8): estado *Revisa plan*. Ratio 7,2:1.

### Neutral
- **Papel Cálido** (#faf8f4): fondo de página.
- **Hoja Blanca** (#ffffff): tarjetas y barra de pestañas; se separa del papel por tono y borde.
- **Tinta Nocturna** (#1b2430): texto principal. 14,8:1 sobre el papel.
- **Tinta Apagada** (#4a5565): texto secundario. 7,1:1 sobre el papel.
- **Línea de Cuaderno** (#ddd8ce): bordes finos decorativos.
- **Línea Firme** (#8a8f98): bordes que delimitan controles (3:1 sobre el papel).

### Named Rules
**The Palabra Con Color Rule.** Un estado se comunica siempre con color y palabra ("Tranquilo", "Atento", "Revisa plan"). El color solo nunca basta.
**The Sin Rojo Rule.** El rojo no existe en el sistema. "Revisa plan" usa índigo precisamente para no alarmar.
**The One Voice Rule.** El azul de acento ocupa menos del 10 % de la pantalla; su escasez es lo que lo hace legible.

## Typography

**Display, cuerpo y etiquetas:** pila del sistema (`ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, …`). Sin fuentes remotas: la demo debe funcionar sin red.

**Character:** neutra, nativa y legible. Cada plataforma muestra su propia tipografía de sistema, a la que el usuario ya está acostumbrado; el carácter sale de la escala y el espacio, no de la fuente.

### Hierarchy
- **Hero** (600, 2.75rem / 44 px, 1.1): la cifra de la portada (patrimonio o impacto).
- **Headline** (600, 2rem / 32 px, 1.2): títulos de página.
- **Title** (600, 1.5rem / 24 px, 1.25): títulos de sección y tarjetas.
- **Body** (400, 1.125rem / 18 px, 1.5): texto corrido. Líneas de 65 caracteres como máximo.
- **Label** (500, 1rem / 16 px, 1.4): pestañas, botones y metadatos. Nunca por debajo de 16 px.

### Named Rules
**The 18 Rule.** Nada de texto legible por debajo de 16 px, y el cuerpo parte de 18 px. Las cifras usan números tabulares cuando se alinean en columna.

## Layout

Móvil primero, pero la app también se usa en escritorio. En móvil (< 1024 px) es una columna de un máximo de 36 rem (576 px) centrada, con 16 px de margen lateral y una barra de tres pestañas fija abajo (Inicio · Cartera · Pregunta). En escritorio (≥ 1024 px, `lg`) la misma barra sube arriba como cabecera fija con la marca a la izquierda, las pestañas marcadas con un filo inferior de 4 px y el enlace al panel a la derecha; el contenido llega a 72 rem (1152 px) con 24 px de margen y puede ir a dos columnas (en Inicio: estado a la izquierda, atajos a la derecha). Es un único `<nav>`, reordenado con CSS. El widget de la pantalla de inicio del móvil es un componente aparte que se hará después. El panel (`/panel`) es un layout de escritorio independiente: cabecera con la marca, contenido hasta 72 rem (1152 px) y 24 px de margen lateral, sin barra inferior.

El ritmo de espacio usa pasos de 8, 16 y 24 px. La altura de pestaña es de 56 px y todo objetivo táctil mide al menos 44×44 px. El texto debe poder ampliarse al 200 % sin perder contenido ni producir desplazamiento horizontal.

## Elevation & Depth

Sistema plano, de capas tonales. La profundidad se transmite con el salto entre el papel cálido (#faf8f4) y la hoja blanca (#ffffff), reforzado con un borde fino (#ddd8ce). No hay sombras. El único elemento "elevado" visualmente es la barra de pestañas, separada por una línea superior.

### Named Rules
**The Flat-By-Default Rule.** Las superficies son planas en reposo y en estado activo. El foco se resuelve con un anillo de 3 px, no con sombra.

## Shapes

Esquinas suaves pero no infantiles: las tarjetas usan 16 px de radio; los controles de entrada táctiles usan el mismo radio. Bordes de 1 px en tono papel oscuro para tarjetas; los controles que necesitan ser localizables usan el borde firme. Las pestañas se marcan con un filo superior de 4 px, no con formas.

## Components

Táctiles y claros: grandes, de un solo gesto y sin adornos.

### Navigation (pestañas inferiores)
- **Style:** tres pestañas iguales, 56 px de alto, texto de 18 px (peso 500), sobre hoja blanca con un filo superior de 1 px.
- **Default:** texto Tinta Apagada, filo transparente.
- **Active:** texto azul, fondo papel, filo superior azul de 4 px (señal doble: color y forma).
- **Hover / Focus:** hover oscurece el texto a Tinta Nocturna; foco con anillo azul de 3 px.

### Cards / Containers (nota vacía y tarjetas)
- **Corner Style:** 16 px.
- **Background:** hoja blanca sobre papel.
- **Shadow Strategy:** ninguna; ver Elevation & Depth.
- **Border:** 1 px Línea de Cuaderno.
- **Internal Padding:** 16 px.

### Estado (insignia de estado del widget)
- **Style:** fondo del color de estado claro, texto del color de estado oscuro, palabra siempre visible ("Tranquilo", "Atento", "Revisa plan").
- **Anuncio:** el cambio por polling se anuncia con `aria-live="polite"`.

### Enlaces
- Azul de acento, subrayados, con zona táctil mínima de 44 px de alto.

## Do's and Don'ts

### Do:
- **Do** usar siempre color y palabra para un estado.
- **Do** mantener todo par texto/fondo en WCAG AA o mejor (los tokens del sistema ya lo cumplen).
- **Do** dar a todo objetivo táctil 44×44 px como mínimo.
- **Do** respetar `prefers-reduced-motion`: sin animaciones esenciales.
- **Do** mostrar una cifra y una frase en pantalla; lo demás, al panel.
- **Do** formatear cifras solo con el helper único de `src/lib/format.ts`.

### Don't:
- **Don't** usar rojo, parpadeos ni iconos de alarma.
- **Don't** transmitir significado solo con el color.
- **Don't** añadir sombras: la profundidad es tonal.
- **Don't** usar fuentes remotas ni librerías de iconos o de componentes sin acordarlo antes.
- **Don't** mostrar cifras inventadas en la interfaz; si no hay dato, estado vacío honesto.
- **Don't** usar texto por debajo de 16 px.
