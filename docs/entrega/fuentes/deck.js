// Presentación de KAIROS para el jurado (T6-02). Cifras: motor real (ver docs/entrega/README.md).
const pptxgen = require("pptxgenjs");

const OUT = process.argv[2] || "KAIROS-presentacion.pptx";
const INK = "1D1A15";
const BRONZE = "765600";
const GOLD = "F2C14E";
const TINT = "F7EDD5";
const PAPER = "F5F3EE";
const MUTED = "5A5246";
const LINE = "E6E0D4";
const WHITE = "FFFFFF";
const GREEN = "145C33";
const RED = "962018";
const HEAD = "Cambria";
const BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.title = "KAIROS: el mundo, traducido a tu cartera";
pres.author = "Equipo KAIROS";
pres.subject = "Hack Finance · BEST UC3M";
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

const W = 13.333;
const M = 0.6;

pres.defineSlideMaster({
  title: "CONTENIDO",
  background: { color: WHITE },
  objects: [
    {
      text: {
        text: "KAIROS · Hack Finance · BEST UC3M",
        options: { x: M, y: 7.05, w: 6, h: 0.3, fontFace: BODY, fontSize: 10, color: MUTED, margin: 0 },
      },
    },
  ],
  slideNumber: { x: W - M - 0.6, y: 7.05, w: 0.6, h: 0.3, fontFace: BODY, fontSize: 10, color: MUTED, align: "right" },
});

pres.defineSlideMaster({ title: "OSCURA", background: { color: INK } });

// Espacio no separable antes de % y € (y tras «entre»/«y» de los rangos no hace falta): la cifra
// nunca se separa de su unidad al partir la línea.
const NBSP = " ";
const fixUnits = (t) => (typeof t === "string" ? t.replace(/ (%|€)/g, `${NBSP}$1`) : t);
const fixRuns = (v) =>
  Array.isArray(v) ? v.map((r) => (r && typeof r === "object" ? { ...r, text: fixUnits(r.text) } : fixUnits(r))) : fixUnits(v);
const rawAddSlide = pres.addSlide.bind(pres);
pres.addSlide = (opts) => {
  const slide = rawAddSlide(opts);
  const addText = slide.addText.bind(slide);
  const addTable = slide.addTable.bind(slide);
  slide.addText = (text, o) => addText(fixRuns(text), o);
  slide.addTable = (rows, o) => addTable(rows.map((row) => row.map((c) => ({ ...c, text: fixUnits(c.text) }))), o);
  return slide;
};

function title(slide, text, sub) {
  slide.addText(text, {
    x: M, y: 0.45, w: W - 2 * M, h: 0.8, fontFace: HEAD, fontSize: 34, bold: true, color: INK, margin: 0,
    isTextBox: true, objectName: "Título",
  });
  if (sub) {
    slide.addText(sub, {
      x: M, y: 1.25, w: W - 2 * M, h: 0.45, fontFace: BODY, fontSize: 16, color: MUTED, margin: 0,
      isTextBox: true, objectName: "Subtítulo",
    });
  }
}

function badge(slide, x, y, label, fill = GOLD, color = INK, d = 0.55) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  slide.addText(label, {
    x, y, w: d, h: d, fontFace: HEAD, fontSize: Math.round(d * 33), bold: true, color, align: "center", valign: "middle",
    margin: 0, isTextBox: true,
  });
}

function card(slide, x, y, w, h, fill = PAPER) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, fill: { color: fill }, line: { color: LINE, width: 1 }, rectRadius: 0.12,
  });
}

function note(slide, text) {
  slide.addText(text, {
    x: M, y: 6.55, w: W - 2 * M, h: 0.4, fontFace: BODY, fontSize: 11, color: MUTED, italic: true,
    margin: 0, isTextBox: true, objectName: "Nota de fuentes",
  });
}

// 1 · Portada -------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "OSCURA" });
  badge(s, M, 1.4, "K", GOLD, INK, 0.9);
  s.addText("KAIROS", {
    x: M, y: 2.5, w: 9, h: 1.3, fontFace: HEAD, fontSize: 72, bold: true, color: WHITE, margin: 0, isTextBox: true,
  });
  s.addText("El mundo, traducido a tu cartera", {
    x: M, y: 3.8, w: 10, h: 0.7, fontFace: HEAD, fontSize: 30, italic: true, color: GOLD, margin: 0, isTextBox: true,
  });
  s.addText(
    "Qué ha pasado, cuánto te afecta en euros y qué significa para tu plan. Sin ruido y sin decirte qué comprar.",
    { x: M, y: 4.75, w: 9.5, h: 0.9, fontFace: BODY, fontSize: 18, color: "D9D2C3", margin: 0, isTextBox: true },
  );
  s.addText("Hack Finance · BEST UC3M · noviembre de 2026", {
    x: M, y: 6.6, w: 8, h: 0.4, fontFace: BODY, fontSize: 14, color: "B8AE9C", margin: 0, isTextBox: true,
  });
  s.addNotes(
    "Invertir se ha vuelto fácil. Entender lo que tienes, y cómo te afecta lo que pasa en el mundo, no. " +
      "KAIROS vigila mercados, noticias y bancos centrales y lo traduce a tu cartera: qué ha pasado, cuánto te " +
      "afecta en euros y qué significa para tu plan. Sin decirte qué comprar.",
  );
}

// 2 · Problema ------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENIDO" });
  title(s, "Las noticias no dicen qué le pasa a tu dinero");
  const stats = [
    ["19,1 M", "cuentas en fondos españoles, frente al 12,2 % de hogares con acciones: se invierte a través de fondos", "CNMV; Encuesta Financiera de las Familias"],
    ["19 %", "de los inversores españoles vendió en la caída del COVID", "ING, vía Funds Society"],
    ["¿Y a mí?", "«El BCE baja los tipos» no dice nada de lo que pasa con tus 40.000 €", "Las noticias hablan del mercado, no de tu cartera"],
  ];
  const cw = (W - 2 * M - 2 * 0.4) / 3;
  stats.forEach(([big, text, src], i) => {
    const x = M + i * (cw + 0.4);
    card(s, x, 1.75, cw, 4.4);
    s.addText(big, {
      x: x + 0.35, y: 2.05, w: cw - 0.7, h: 1.3, fontFace: HEAD, fontSize: 60, bold: true, color: BRONZE,
      margin: 0, isTextBox: true,
    });
    s.addText(text, {
      x: x + 0.35, y: 3.45, w: cw - 0.7, h: 1.7, fontFace: BODY, fontSize: 17, color: INK, margin: 0,
      valign: "top", isTextBox: true,
    });
    s.addText(src, {
      x: x + 0.35, y: 5.35, w: cw - 0.7, h: 0.6, fontFace: BODY, fontSize: 11, color: MUTED, margin: 0,
      valign: "top", isTextBox: true,
    });
  });
  note(s, "Quien combina un MSCI World, un S&P 500 y un fondo tecnológico cree estar diversificado y puede estar muy concentrado.");
  s.addNotes(
    "En España se invierte sobre todo con fondos. El inversor no sabe lo que tiene dentro ni cómo le afecta lo " +
      "que pasa: las noticias hablan del mercado. Y cuando cae la bolsa, uno de cada cinco vende en pánico.",
  );
}

// 3 · Solución ------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENIDO" });
  title(s, "Tres niveles: una frase, una pregunta y un panel", "Cada evento se traduce a euros de tu cartera y se cruza con tu propio plan");
  const items = [
    ["1", "Widget", "Una cifra y una frase. Tres estados: Tranquilo, Atento y Revisa tu plan. Si no hay aviso, no hay nada que hacer."],
    ["2", "Voz", "Pulsas y preguntas «¿por qué ha bajado?» o «¿voy bien?». Responde con la cadena causal y la cifra en euros."],
    ["3", "Panel de contexto", "Eventos traducidos a tu cartera, exposición real dentro de los fondos, radar de riesgos y la traza de cada cifra."],
    ["4", "Avisos que importan", "Como mucho 2 por semana, solo si un evento te toca de verdad o te alejas de tu plan."],
  ];
  const cw = (W - 2 * M - 0.4) / 2;
  items.forEach(([n, head, text], i) => {
    const x = M + (i % 2) * (cw + 0.4);
    const y = 2.0 + Math.floor(i / 2) * 2.25;
    card(s, x, y, cw, 1.95);
    badge(s, x + 0.3, y + 0.3, n);
    s.addText(head, {
      x: x + 1.05, y: y + 0.28, w: cw - 1.35, h: 0.55, fontFace: HEAD, fontSize: 22, bold: true, color: INK,
      margin: 0, isTextBox: true,
    });
    s.addText(text, {
      x: x + 1.05, y: y + 0.85, w: cw - 1.35, h: 0.95, fontFace: BODY, fontSize: 16, color: INK, margin: 0,
      valign: "top", isTextBox: true,
    });
  });
  s.addNotes(
    "Por fuera, simple: una frase en el widget, una pregunta por voz y un panel para quien quiera profundizar. " +
      "Por dentro, agentes y motores que el usuario no ve.",
  );
}

// 4 · Radiografía ---------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENIDO" });
  title(s, "Laura cree que está diversificada", "Radiografía de su cartera mirando dentro de cada fondo (look-through)");
  const stats = [
    ["63,7 %", "de su dinero está en Estados Unidos"],
    ["25,9 %", "en solo 7 empresas, repetidas en varios fondos"],
    ["76,0 %", "en renta variable, frente al 70 % de su plan"],
  ];
  const cw = (W - 2 * M - 2 * 0.4) / 3;
  stats.forEach(([big, text], i) => {
    const x = M + i * (cw + 0.4);
    card(s, x, 2.0, cw, 3.2, i === 1 ? TINT : PAPER);
    s.addText(big, {
      x: x + 0.35, y: 2.35, w: cw - 0.7, h: 1.4, fontFace: HEAD, fontSize: 64, bold: true, color: BRONZE,
      margin: 0, isTextBox: true,
    });
    s.addText(text, {
      x: x + 0.35, y: 3.85, w: cw - 0.7, h: 1.1, fontFace: BODY, fontSize: 18, color: INK, margin: 0,
      valign: "top", isTextBox: true,
    });
  });
  s.addText("Apple y NVIDIA están en sus acciones y, a la vez, dentro de sus dos fondos de bolsa mundial; Microsoft, Alphabet y Amazon, en los dos fondos.", {
    x: M, y: 5.5, w: W - 2 * M, h: 0.7, fontFace: BODY, fontSize: 16, color: INK, margin: 0, isTextBox: true,
  });
  note(s, "Cartera de ejemplo ilustrativa (42.364 €) con precios de cierre reales del 6-nov-2026 y composiciones publicadas por las gestoras. Calculado por el motor de exposición de KAIROS.");
  s.addNotes(
    "Paso 2 del guion. Laura tiene tres fondos y cuatro acciones. KAIROS mira dentro de cada fondo: casi dos tercios " +
      "de su dinero está en Estados Unidos y una cuarta parte en siete empresas que se repiten.",
  );
}

// 5 · Misma noticia, dos carteras -------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENIDO" });
  title(s, "La misma noticia no significa lo mismo para todos", "Impacto estimado el día de cada evento, con su rango");
  const hdr = (t, align = "left") => ({
    text: t, options: { bold: true, color: WHITE, fill: { color: INK }, fontFace: BODY, fontSize: 15, align, valign: "middle" },
  });
  const cell = (t, opts = {}) => ({ text: t, options: { fontFace: BODY, fontSize: 15, color: INK, valign: "middle", ...opts } });
  const rows = [
    [hdr("Evento real"), hdr("Laura · 42.364 € · 76 % renta variable"), hdr("Javier · 180.000 € · 65 % renta fija")],
    [
      cell("El BCE baja los tipos\n5 jun 2025", { bold: true }),
      cell("entre −89 € y −73 €  (−0,19 %)"),
      cell("entre −243 € y −206 €  (−0,12 %)"),
    ],
    [
      cell("El petróleo sube un 7 %\n13 jun 2025", { bold: true }),
      cell("entre −250 € y −207 €  (−0,54 %)"),
      cell("entre −451 € y −352 €  (−0,22 %)"),
    ],
    [
      cell("Resultados de NVIDIA\n26 feb 2025", { bold: true }),
      cell("entre −349 € y −325 €  (−0,80 %)", { fill: { color: TINT }, bold: true }),
      cell("entre −273 € y −206 €  (−0,13 %)"),
    ],
  ];
  s.addTable(rows, {
    x: M, y: 1.95, w: W - 2 * M, colW: [3.6, 4.27, 4.26], rowH: [0.6, 0.95, 0.95, 0.95],
    border: { type: "solid", color: LINE, pt: 1 }, fill: { color: WHITE }, margin: 0.12, objectName: "Tabla de impactos",
  });
  s.addText("NVIDIA le cuesta a Laura seis veces más, en proporción, que a Javier: la tiene en acciones y dentro de dos fondos.", {
    x: M, y: 5.75, w: W - 2 * M, h: 0.6, fontFace: BODY, fontSize: 16, color: INK, margin: 0, isTextBox: true,
  });
  note(s, "Carteras de ejemplo ilustrativas; movimientos reales del mercado de cada día. Cifras del motor de impacto (betas por factor sobre 3 años de cierres diarios), cada una con su calc_id.");
  s.addNotes(
    "Golpe de personalización. Tres eventos reales y dos carteras. Siempre en rango, nunca una cifra exacta. " +
      "Los números los calcula el motor determinista; Claude solo los explica.",
  );
}

// 6 · Arquitectura --------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENIDO" });
  title(s, "Arquitectura: la IA explica, los motores calculan");
  const top = 1.55;
  const colH = 4.75;
  // Columna 1: fuentes
  const c1x = M, c1w = 2.75;
  card(s, c1x, top, c1w, colH, PAPER);
  s.addText("Fuentes", { x: c1x + 0.25, y: top + 0.2, w: c1w - 0.5, h: 0.45, fontFace: HEAD, fontSize: 18, bold: true, color: BRONZE, margin: 0, isTextBox: true });
  s.addText(
    [
      { text: "Precios y factores", options: { bold: true, breakLine: true } },
      { text: "Yahoo Finance y BCE", options: { breakLine: true } },
      { text: " ", options: { breakLine: true, fontSize: 8 } },
      { text: "Eventos reales", options: { bold: true, breakLine: true } },
      { text: "BCE, petróleo, resultados", options: { breakLine: true } },
      { text: " ", options: { breakLine: true, fontSize: 8 } },
      { text: "Composición de fondos", options: { bold: true, breakLine: true } },
      { text: "Ficheros de las gestoras", options: {} },
    ],
    { x: c1x + 0.25, y: top + 0.8, w: c1w - 0.5, h: 3.6, fontFace: BODY, fontSize: 14, color: INK, margin: 0, valign: "top", isTextBox: true },
  );
  // Columna 2: backend
  const c2x = c1x + c1w + 0.55, c2w = 5.6;
  card(s, c2x, top, c2w, colH, WHITE);
  s.addText("Backend · FastAPI + PostgreSQL", { x: c2x + 0.25, y: top + 0.2, w: c2w - 0.5, h: 0.45, fontFace: HEAD, fontSize: 18, bold: true, color: BRONZE, margin: 0, isTextBox: true });
  const box = (x, y, w, h, head, sub, lines, fill) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: LINE, width: 1 }, rectRadius: 0.08 });
    s.addText(head, { x: x + 0.18, y: y + 0.14, w: w - 0.36, h: 0.36, fontFace: BODY, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
    s.addText(sub, { x: x + 0.18, y: y + 0.5, w: w - 0.36, h: 0.3, fontFace: BODY, fontSize: 12, italic: true, color: MUTED, margin: 0, isTextBox: true });
    s.addText(lines, { x: x + 0.18, y: y + 0.95, w: w - 0.36, h: h - 1.05, fontFace: BODY, fontSize: 13, color: INK, margin: 0, valign: "top", paraSpaceAfter: 4, isTextBox: true });
  };
  const half = (c2w - 0.5 - 0.25) / 2;
  box(c2x + 0.25, top + 0.8, half, 2.85, "Calculan", "motores deterministas",
    "Gestor de cartera: FIFO, traspasos, DCA\nExposición mirando dentro de los fondos\nMotor de impacto: betas por factor y rangos", PAPER);
  box(c2x + 0.25 + half + 0.25, top + 0.8, half, 2.85, "Explican", "agentes con Claude",
    "Analizador de eventos: cadena causal\nExplicador con herramientas sobre la cartera\nGuardián: sin órdenes, cifras verificadas", TINT);
  s.addText("Cada cifra lleva un calc_id con sus entradas, fórmula y fuentes", {
    x: c2x + 0.25, y: top + 3.8, w: c2w - 0.5, h: 0.6, fontFace: BODY, fontSize: 14, italic: true, color: MUTED, margin: 0, isTextBox: true,
  });
  // Columna 3: app
  const c3x = c2x + c2w + 0.55, c3w = W - M - c3x;
  card(s, c3x, top, c3w, colH, PAPER);
  s.addText("App · React", { x: c3x + 0.25, y: top + 0.2, w: c3w - 0.5, h: 0.45, fontFace: HEAD, fontSize: 18, bold: true, color: BRONZE, margin: 0, isTextBox: true });
  s.addText(
    [
      { text: "Widget", options: { bold: true, breakLine: true } },
      { text: "Estado y frase precalculados", options: { breakLine: true } },
      { text: " ", options: { breakLine: true, fontSize: 8 } },
      { text: "Voz", options: { bold: true, breakLine: true } },
      { text: "ElevenLabs: voz a texto y texto a voz", options: { breakLine: true } },
      { text: " ", options: { breakLine: true, fontSize: 8 } },
      { text: "Panel", options: { bold: true, breakLine: true } },
      { text: "Eventos, exposición y trazas", options: {} },
    ],
    { x: c3x + 0.25, y: top + 0.8, w: c3w - 0.5, h: 3.6, fontFace: BODY, fontSize: 14, color: INK, margin: 0, valign: "top", isTextBox: true },
  );
  // Flechas entre columnas
  const ay = top + colH / 2;
  s.addShape(pres.shapes.LINE, { x: c1x + c1w + 0.08, y: ay, w: 0.4, h: 0, line: { color: BRONZE, width: 2.5, endArrowType: "triangle" } });
  s.addShape(pres.shapes.LINE, { x: c2x + c2w + 0.08, y: ay, w: 0.4, h: 0, line: { color: BRONZE, width: 2.5, endArrowType: "triangle" } });
  note(s, "Docker Compose arranca base de datos, backend y app con datos de ejemplo. Modo demo con eventos reales reproducidos; modo producción con precios en directo.");
  s.addNotes(
    "Tres fuentes, un backend con dos mitades y una app. Los motores deterministas calculan todas las cifras; " +
      "los agentes de Claude entienden la noticia y redactan, y el guardián revisa cada frase antes de que llegue " +
      "al usuario. Si el LLM falla, hay plantillas: la cifra nunca depende de él.",
  );
}

// 7 · Confianza -----------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENIDO" });
  title(s, "Pensado para merecer confianza", "Contexto, no órdenes: compatible con MiFID II y con el AI Act");
  const stats = [
    ["0", "órdenes de compraventa en 30 preguntas a Claude real, 10 de ellas trampa («¿vendo?»)"],
    ["1,7 s", "hasta la primera palabra hablada (mediana; por debajo de 2 s en 9 de cada 10)"],
    ["1 traza", "por cada cifra: entradas, fórmula y fuentes. El LLM no calcula ninguna; solo redacta"],
  ];
  const cw = (W - 2 * M - 2 * 0.4) / 3;
  stats.forEach(([big, text], i) => {
    const x = M + i * (cw + 0.4);
    card(s, x, 2.0, cw, 2.75);
    s.addText(big, { x: x + 0.35, y: 2.25, w: cw - 0.7, h: 1.1, fontFace: HEAD, fontSize: 54, bold: true, color: BRONZE, margin: 0, isTextBox: true });
    s.addText(text, { x: x + 0.35, y: 3.4, w: cw - 0.7, h: 1.2, fontFace: BODY, fontSize: 16, color: INK, margin: 0, valign: "top", isTextBox: true });
  });
  s.addText(
    [
      { text: "Nunca «compra» ni «vende»: las oportunidades se expresan frente a las reglas del propio usuario (su plan, su DCA).", options: { bullet: true, breakLine: true } },
      { text: "Aviso de IA visible en la app y al empezar la voz; aviso «no es asesoramiento» en el panel.", options: { bullet: true, breakLine: true } },
      { text: "Rangos con nivel de confianza, nunca una cifra exacta.", options: { bullet: true } },
    ],
    { x: M, y: 5.0, w: W - 2 * M, h: 1.4, fontFace: BODY, fontSize: 16, color: INK, margin: 0, paraSpaceAfter: 6, valign: "top", isTextBox: true },
  );
  s.addNotes(
    "El riesgo de este producto es cruzar la línea del asesoramiento. El guardián bloquea cualquier orden y comprueba " +
      "que cada cifra coincide con la del motor. Lo medimos: cero órdenes en 30 preguntas con Claude real.",
  );
}

// 8 · Diferencial ---------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENIDO" });
  title(s, "Lo que nadie hace en Europa", "Perplexity, Robinhood u OpenAI conectan carteras a una IA, pero en EE. UU. y para acciones");
  const rows = [
    ["Mira dentro de los fondos", "Avisa de unos resultados aunque la empresa esté dentro de tu fondo indexado"],
    ["Avisa sin que preguntes", "En euros de tu cartera y con la cadena causal, no solo una puntuación de riesgo"],
    ["Del evento a tu plan", "Cada noticia se cruza con tu objetivo y tus aportaciones: «¿sigo bien?»"],
    ["Hecho para España", "Fondos y planes de pensiones, traspasos sin tributar, FIFO, valor liquidativo"],
  ];
  rows.forEach(([head, text], i) => {
    const y = 1.95 + i * 1.12;
    badge(s, M, y + 0.12, String(i + 1));
    s.addText(head, { x: M + 0.85, y, w: 4.2, h: 0.8, fontFace: HEAD, fontSize: 20, bold: true, color: INK, margin: 0, valign: "middle", isTextBox: true });
    s.addText(text, { x: M + 5.2, y, w: W - 2 * M - 5.2, h: 0.8, fontFace: BODY, fontSize: 16, color: INK, margin: 0, valign: "middle", isTextBox: true });
  });
  note(s, "Competidor más cercano: Ripplora (terminal para operar, centrado en EE. UU., sin mirar dentro de los fondos).");
  s.addNotes(
    "La idea está validada fuera. En Europa, donde se invierte con fondos, nadie traduce el mundo a tu cartera. " +
      "Frente a Ripplora: no somos un terminal para operar, somos para quien no quiere vivir pendiente del mercado.",
  );
}

// 9 · Negocio -------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "CONTENIDO" });
  title(s, "Negocio: marca blanca para brókers", "La vía principal es B2B2C; la versión de consumo valida el producto");
  const cw = (W - 2 * M - 0.4) / 2;
  const blocks = [
    ["B2B2C · vía principal", "Licencia por usuario activo al mes para brókers, neobancos y gestoras de indexados.", "Al bróker le interesa que su cliente no venda en pánico y siga aportando. Y ya tiene la cartera: no hay que conectar datos.", TINT],
    ["B2C freemium · validación", "Gratis: widget y 1-2 avisos por semana. De pago: voz sin límite, escenarios y panel completo.", "Crea demanda y valida el producto antes de vender a entidades.", PAPER],
  ];
  blocks.forEach(([head, a, b, fill], i) => {
    const x = M + i * (cw + 0.4);
    card(s, x, 2.0, cw, 3.1, fill);
    s.addText(head, { x: x + 0.35, y: 2.25, w: cw - 0.7, h: 0.55, fontFace: HEAD, fontSize: 22, bold: true, color: BRONZE, margin: 0, isTextBox: true });
    s.addText(a, { x: x + 0.35, y: 2.9, w: cw - 0.7, h: 1.0, fontFace: BODY, fontSize: 17, color: INK, margin: 0, valign: "top", isTextBox: true });
    s.addText(b, { x: x + 0.35, y: 3.95, w: cw - 0.7, h: 1.0, fontFace: BODY, fontSize: 15, color: MUTED, margin: 0, valign: "top", isTextBox: true });
  });
  s.addText("Coste por usuario bajo: cada evento se analiza una vez con el modelo potente y sirve para todos; por usuario solo se calcula el impacto (determinista) y se redactan frases cortas con un modelo rápido.", {
    x: M, y: 5.45, w: W - 2 * M, h: 0.9, fontFace: BODY, fontSize: 16, color: INK, margin: 0, valign: "top", isTextBox: true,
  });
  s.addNotes(
    "La vía principal es B2B2C. GPTadvisor ya vende a entidades «sube tu cartera y habla con una IA», así que hay " +
      "demanda. Nuestra diferencia: avisamos sin que preguntes, en euros, mirando dentro de los fondos y por voz.",
  );
}

// 10 · Cierre -------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "OSCURA" });
  s.addText("Hecho y funcionando", {
    x: M, y: 1.1, w: W - 2 * M, h: 0.9, fontFace: HEAD, fontSize: 44, bold: true, color: WHITE, margin: 0, isTextBox: true,
  });
  s.addText(
    [
      { text: "docker compose up arranca todo con datos de ejemplo; el README explica cómo probarlo.", options: { bullet: true, breakLine: true } },
      { text: "Más de 2.200 tests automáticos en backend y frontend; casos dorados del gestor de cartera y del motor de impacto.", options: { bullet: true, breakLine: true } },
      { text: "Ya en marcha hacia producción: precios en directo, varias carteras e impacto medido tras el cierre de cada día.", options: { bullet: true } },
    ],
    { x: M, y: 2.3, w: 11.5, h: 2.4, fontFace: BODY, fontSize: 20, color: "E8E2D6", margin: 0, paraSpaceAfter: 10, valign: "top", isTextBox: true },
  );
  s.addText("KAIROS · el mundo, traducido a tu cartera", {
    x: M, y: 5.6, w: W - 2 * M, h: 0.7, fontFace: HEAD, fontSize: 28, italic: true, color: GOLD, margin: 0, isTextBox: true,
  });
  s.addText("Información, no asesoramiento. Las respuestas las genera una IA.", {
    x: M, y: 6.6, w: W - 2 * M, h: 0.4, fontFace: BODY, fontSize: 13, color: "B8AE9C", margin: 0, isTextBox: true,
  });
  s.addNotes("Cierre: producto acabado, ejecutable y con tests. Gracias. Preguntas.");
}

pres.writeFile({ fileName: OUT }).then((f) => console.log("escrito:", f));
