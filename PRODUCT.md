# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Principal: Laura, 34.** Inversora de 25-45 años, nivel intermedio, con fondos indexados y alguna acción. No tiene tiempo ni ganas de seguir los mercados y se pone nerviosa con los titulares de caídas. Abre el widget o la app en el móvil para saber, en una frase, si le afecta algo y si tiene que hacer algo (casi nunca).

**Secundario: Javier, 58.** Inversor cercano a la jubilación, más conservador, que usa sobre todo la voz. De él vienen los requisitos de accesibilidad: texto grande, contraste alto y voz como vía principal.

Móvil primero: widget y app. `/panel` es la vista de escritorio para quien quiere profundizar.

## Product Purpose

KAIROS traduce eventos financieros (BCE, petróleo, resultados, divisas) al impacto en euros sobre la cartera de un inversor particular: qué le afecta, cuánto y si su plan sigue en pie. Tagline: "El mundo, traducido a tu cartera." Éxito: el usuario entiende en segundos cómo le afecta lo que pasa y no actúa por pánico.

## Positioning

Impacto proactivo en euros sobre la cartera real (con look-through de fondos y ETF) más voz, expresado frente al plan del propio usuario. No es un agregador de noticias ni un asesor: da contexto, no órdenes.

## Operating Context

Proyecto de hackathon (Hack Finance, BEST UC3M), 4 días, demo de menos de 3 minutos con carteras de ejemplo (Laura y Javier) y eventos en modo replay. Capas de menos a más detalle: widget, pregunta por voz, aviso solo cuando importa y panel de contexto.

## Capabilities and Constraints

- Frontend: React + Vite + TypeScript estricto + Tailwind + TanStack Query. Llamadas al backend solo desde `src/api/` con los tipos generados.
- El LLM nunca calcula cifras: todo número viene del backend. El frontend solo formatea. Los importes llegan como string Decimal.
- Estados del widget: `tranquilo`, `atento`, `revisa_plan`.
- Textos visibles en español de España.
- Aviso de IA visible (AI Act art. 50) y aviso de "no es asesoramiento" en el panel.
- Las operaciones son registros, no órdenes reales.

## Brand Commitments

Nombre KAIROS. Tono tranquilo, directo, sin urgencia gratuita. Sin rojos alarmistas.

## Evidence on Hand

Prototipo de referencia enlazado en `docs/kairos-spec.md`. No hay aún datos reales en `data/seed/`; no se deben inventar cifras en la UI. Los datos de ejemplo llevan `"illustrative": true`.

## Product Principles

1. **Personalización total.** Cada mensaje habla de su cartera; si un evento no la toca, no se ve.
2. **Menos es más.** Una cifra y una frase en pantalla; lo que no cabe va al panel.
3. **Siempre en euros de su cartera.** Nunca "el mercado cae un 2%".
4. **Contexto, no órdenes.** Nunca "compra" ni "vende"; riesgos y oportunidades frente a las reglas del propio usuario.
5. **Calmar antes que alarmar.** El silencio también es información; nada de rojos ni urgencia gratuita.
6. **Todo es verificable.** Cada cifra tiene un "¿de dónde sale?". Los impactos estimados se muestran como rango con confianza; el patrimonio y las posiciones, como cifra exacta con la fecha del precio.
7. **Por dentro complejo, por fuera simple.**
8. **Estados con color + palabra**, nunca solo color.
9. **La voz es una vía principal**, no un extra.

## Accessibility & Inclusion

- WCAG AA como mínimo; texto base 18 px en móvil.
- Objetivos táctiles de al menos 44×44 px.
- Ningún significado solo por color.
- Respetar `prefers-reduced-motion`.
- Soporte de lector de pantalla; el cambio de estado del widget (por polling) se anuncia con `aria-live="polite"`.
- Zoom del texto hasta 200 % sin pérdida de contenido ni scroll horizontal.
- La transcripción de la voz y el texto de la respuesta siempre visibles en pantalla, no solo audio.
