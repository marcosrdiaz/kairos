# KAIROS — Idea de proyecto (Hack Finance)

Nov 8, 2026 · @Manuel · Hack Finance · 4 días · Claude + ElevenLabs · Documento vivo para ir definiendo features, alcance y arquitectura

## Resumen

KAIROS traduce lo que pasa en el mundo financiero al impacto concreto en tu cartera: qué te afecta, cuánto en euros y qué riesgos u oportunidades abre según tu plan, de forma completamente personalizada.

**Idea central.** La misma noticia no significa lo mismo para todos. Una bajada de tipos del BCE, una caída de las tecnológicas o un dólar débil afectan de forma distinta a cada cartera. KAIROS centraliza la información y el análisis del mundo financiero y lo filtra por tu perfil para que veas solo lo que te toca, cómo te toca y si tienes que hacer algo (casi nunca).

**Elevator pitch**

> Invertir se ha vuelto fácil. Entender lo que tienes, y cómo te afecta lo que pasa en el mundo, no. KAIROS vigila los mercados, las noticias y los bancos centrales por ti y lo traduce a tu cartera: qué ha pasado, cuánto te afecta en euros y qué riesgos u oportunidades abre según tu plan. Lo ves en una frase en tu móvil, lo preguntas por voz ("¿por qué ha bajado?", "¿me afecta lo del BCE?", "¿voy bien?") y, si quieres profundizar, tienes un panel con todo tu contexto. Sin ruido y sin decirte qué comprar.

**Tagline:** "El mundo, traducido a tu cartera." (alternativa: "Tu patrimonio, en una frase.")

**Cómo funciona en un párrafo.** Al descargar la app, el usuario da de alta su cartera (activos, participaciones y precio medio), su perfil y sus aportaciones periódicas (DCA), y registra sus compras, ventas y traspasos. KAIROS valora la cartera en tiempo real y mira dentro de cada fondo para conocer la exposición real. Un equipo de agentes de IA vigila noticias, bancos centrales, resultados y datos macro; un motor de cálculo traduce cada evento a euros de esa cartera; y el usuario lo recibe en tres niveles: una frase en el widget, una respuesta por voz y un panel de contexto para profundizar. Los avisos solo llegan cuando algo importa o cuando se desvía del plan que él mismo se marcó.

**Prototipo:** [KAIROS — Prototipo de la app](https://claude.ai/artifact/Wa1t6cdue24SoaVFRCkzGK) (widget, app móvil y panel web, con datos de ejemplo).

## Hackathon: criterios, entregables y plan de 4 días

El jurado evalúa con una rúbrica cerrada. El 60% del peso está en innovación/viabilidad (30%) e implementación (30%): gana un producto **acabado y que funciona**, no el que tiene más features. Todo lo que no se vea en la demo no puntúa.

### Cómo responde KAIROS a la rúbrica

| Criterio | Peso | Qué mira el jurado | Cómo lo cubre KAIROS | Dónde se ve en la demo |
| --- | --- | --- | --- | --- |
| Innovación y viabilidad | 30% | Problema real, solución útil, viable financieramente, novedosa frente al mercado | El inversor en fondos indexados no sabe qué le hace a su dinero lo que pasa en el mundo. KAIROS lo traduce a euros y a su plan. Modelo B2B2C con brókers y neobancos (ver *Modelo de negocio*). Diferencial: impacto proactivo en € + look-through de fondos + voz, para el inversor a largo plazo en España | Misma noticia, dos carteras: dos impactos distintos |
| IA frontera | 15% | Lenguaje y audio avanzados con impacto **medible** en usabilidad, interactividad o accesibilidad | Claude razona la cadena causal (evento → canal → activo → €) con herramientas sobre la cartera real; el guardián valida cada respuesta. ElevenLabs permite preguntar por voz y escuchar la respuesta. Medimos: tiempo para responder «¿cómo me afecta esto?» con voz frente a navegar la app, y tareas completadas por un usuario mayor | Javier pregunta por voz y oye la respuesta en \~2 s |
| UX y accesibilidad | 15% | Interfaz clara e intuitiva; tiempos de respuesta razonables | Widget con 3 estados y una frase; voz como vía principal para mayores; textos grandes y contraste alto. Objetivos de latencia en la tabla de abajo | Widget → detalle → voz sin explicaciones |
| Implementación técnica | 30% | Solución acabada, madura, funcional y lista para ejecutar | Alcance recortado; `docker compose up` arranca todo con datos de ejemplo; tests del motor de cartera y de impacto; ninguna cifra sale del LLM | El jurado puede clonar y ejecutar con el README |
| Presentación | 10% | Problema, solución y arquitectura claros; impacto y diferencial; tiempo y respuestas | Guion de demo de 8 pasos, diapositiva de arquitectura, respuestas preparadas (regulación, Ripplora, de dónde salen las cifras) | Ensayada 3 veces con cronómetro |

### Objetivos de latencia

| Interacción | Objetivo | Cómo se consigue |
| --- | --- | --- |
| Abrir el widget o la app | < 1 s | Estado y frase precalculados en el backend |
| Valorar la cartera tras una operación | < 300 ms | Cálculo determinista en el gestor de cartera, sin LLM |
| Primera palabra de la respuesta por voz | < 2 s | Scribe v2 Realtime + Claude rápido en streaming + Flash v2.5 |
| Explicación escrita de un evento | < 3 s | El análisis pesado del evento se hace al llegar, no cuando el usuario pregunta |
| Escenario («bolsa −10%») | < 500 ms | Betas ya calculadas; solo se multiplica |

### Entregables

- [ ] Repositorio de GitHub público (o compartido con la organización)
- [ ] ZIP descargado desde GitHub (Code → Download ZIP): es la versión oficial
- [ ] README.md: descripción, requisitos, instalación, configuración (claves de Claude y ElevenLabs en `.env.example`), ejecución y prueba
- [ ] PDF de una cara: problema, solución y valor diferencial
- [ ] Presentación PowerPoint para el jurado
- [ ] La demo corresponde exactamente a la versión entregada (sin cambios después del ZIP)
- [ ] Enviar por el formulario oficial de BEST UC3M antes del cierre; se evalúa la última entrega completa

### Plan de 4 días

| Día | Objetivo | Qué tiene que funcionar al final del día |
| --- | --- | --- |
| 1 · Cimientos | Repo, Docker Compose, modelo de datos, datos de ejemplo | Alta de cartera por ISIN; look-through de \~10 fondos y ETFs; 3-4 eventos reales preparados en modo replay; esqueleto de la app con las 3 pestañas |
| 2 · Motores | Gestor de cartera y motor de impacto | Comprar, vender y traspasar con validación fiscal; DCA; impacto en € con rango; agente explicador con Claude y sus herramientas; guardián activo |
| 3 · Experiencia | Voz, widget, avisos y panel | Pregunta por voz de punta a punta con ElevenLabs; widget con 3 estados; panel de contexto; **18:00: el guion de demo funciona entero** |
| 4 · Cierre | Congelar y entregar | Por la mañana solo arreglos y pulido; tests, README, PDF, PowerPoint; ensayo de la demo 3 veces; vídeo de respaldo; ZIP desde GitHub y entrega con margen |

**Regla de alcance.** El MVP es el de la sección *Features*. Lo marcado como «Si da tiempo» solo entra si el día 3 a las 18:00 la demo funciona de punta a punta. Si algo va mal, se recorta antes de llegar a voz, widget y motor de impacto, que son lo que se enseña.

**Reparto sugerido.** Una persona en backend y motores (cartera, impacto), una en agentes (Claude, herramientas, guardián, eventos), una en frontend (widget, app, panel) y una en voz, datos y entregables (ElevenLabs, dataset, README, PDF, PowerPoint). Se adapta al tamaño real del equipo.

## Problema

El inversor minorista tiene más información que nunca, pero ninguna sobre lo que le importa: cómo afecta lo que pasa a su propio patrimonio.

### Problema financiero

1. **No sabe lo que tiene.** En España se invierte sobre todo a través de fondos: solo el 12,2% de los hogares tiene acciones cotizadas directamente ([Encuesta Financiera de las Familias, vía Artículo 14](https://www.articulo14.es/economia/los-inversores-extranjeros-ya-poseen-el-504-de-la-bolsa-espanola-blackrock-vanguard-y-capital-group-suman-100-000-millones-20261015.html)), frente a 19,1 millones de cuentas en fondos españoles y 12,7 millones en IIC extranjeras ([CNMV, vía RankiaPro](https://rankiapro.com/es/noticias/iic-extranjeras-patrimonio-fondos-espanoles/)). Quien combina un MSCI World, un S&P 500 y un fondo tecnológico cree estar diversificado y puede estar muy concentrado.
2. **No sabe cómo le afecta lo que pasa.** Las noticias hablan del mercado, no de su cartera: "el BCE baja tipos" no dice nada sobre sus 40.000 €.
3. **Decide a ciegas, y eso cuesta.** Morningstar estima que en la última década los inversores dejaron de ganar en torno al 12% de la rentabilidad de sus fondos y ETFs por el momento de sus compras y ventas ([Mind the Gap 2026](https://wealthmanagement.com/investing-strategies/investors-miss-out-on-12-of-fund-returns-over-decade)). La cifra está discutida: un estudio de 2026 la rebaja al 0,10% anual ([Financial Analysts Journal](https://rpc.cfainstitute.org/research/financial-analysts-journal/2026/bad-timing-does-not-cost-investors-funds-returns)).
4. **El inversor español es vulnerable al pánico.** Un estudio de ING lo describe como conservador y con conocimientos limitados; en la caída del COVID un 19% vendió ([Funds Society](https://www.fundssociety.com/es/?p=141777)).
5. **El asesoramiento personalizado es caro** o depende del producto que el banco quiera vender.

### Problema técnico

1. **Precios en tiempo real con fuentes mezcladas.** Acciones y ETFs cotizan durante el día, pero los fondos publican un único valor liquidativo diario: la valoración debe combinar ambos y decir de cuándo es cada precio.
2. **Libro de operaciones fiable.** Compras, ventas, traspasos y aportaciones DCA deben recalcular participaciones, precio medio y plusvalías sin errores, con un motor determinista y nunca con el LLM.
3. **Look-through de fondos.** Resolver ISIN → composición → empresas, sectores, países y divisas, y agregarlo en una exposición real.
4. **De la noticia a la exposición.** Extraer eventos estructurados (entidades, tipo, sorpresa frente a lo esperado), eliminar duplicados y vincularlos a las posiciones del usuario.
5. **Cuantificar sin alucinar.** El impacto lo calcula un motor determinista (sensibilidades por factor, casos históricos) que devuelve rangos con confianza; el LLM solo lo explica.
6. **Señal frente a ruido.** Puntuar la relevancia de cada aviso y limitar cuántos se envían.
7. **Voz con baja latencia.** Respuestas de 15-20 segundos, cortas y siempre con una cifra en euros.
8. **Cumplimiento por diseño.** Explicaciones trazables, ninguna salida que sea una recomendación de compraventa y aviso de que se habla con una IA.

## Usuario objetivo

El usuario principal es un inversor de 25-45 años con fondos indexados y alguna acción, de nivel intermedio, que no tiene tiempo ni ganas de seguir los mercados.

**Persona: Laura, 34 años, Madrid.** Ingeniera, invierte 300 € al mes en dos fondos indexados y tiene algunas acciones en un bróker. Tiene unos 40.000 € repartidos en tres sitios. Cuando ve titulares de caídas se pone nerviosa y no sabe si debe hacer algo.

**Persona secundaria: Javier, 58 años, Valencia.** Se jubila en unos 5 años. Tiene unos 180.000 €, sobre todo en fondos de renta fija, un plan de pensiones y un depósito. Le preocupa perder lo ahorrado justo antes de jubilarse.

**La misma noticia, dos carteras** (ejemplos ilustrativos)

| Evento | Laura (renta variable 76%) | Javier (renta fija 65%) |
| --- | --- | --- |
| El BCE baja los tipos 0,25 puntos | +90 €. Poco efecto: solo el 24% de su cartera es renta fija. | Le favorece en sus fondos de renta fija, pero su depósito rentará menos cuando lo renueve. |
| Las tecnológicas de EE. UU. caen un 4,5% | −267 €. Normal para su perfil; el 33% de su cartera está expuesto. | Apenas le afecta: menos del 5% de su dinero está en tecnológicas. |
| El dólar cae un 5% frente al euro | −1.295 €. Es su mayor riesgo después de la bolsa: el 61% está en dólares. | Efecto menor: la mayor parte de su dinero está en euros. |

**Casos de uso**

| Tipo | Necesidad | Ejemplo | Qué hace KAIROS | Dónde |
| --- | --- | --- | --- | --- |
| Entender | Saber cómo va mi patrimonio de un vistazo | "¿Cómo voy?" | Cifra, frase y estado | Widget |
| Entender | Saber por qué se ha movido mi cartera | "¿Por qué ha bajado esta semana?" | Atribuye el movimiento a activos y eventos, en euros | Voz, panel |
| Entender | Saber qué tengo de verdad | "Tengo 3 fondos, ¿estoy diversificado?" | Mira dentro de los fondos: región, sector, divisa y empresas repetidas | Panel |
| Impacto del mundo | Decisión de un banco central | "¿Me afecta lo del BCE?" | Cadena causal y euros con rango | Voz, aviso, panel |
| Impacto del mundo | Resultados de una empresa que tengo, aunque sea dentro de un fondo | Caen las tecnológicas tras resultados | Calcula el impacto aunque la empresa esté dentro de un fondo | Aviso, panel |
| Impacto del mundo | Movimiento de divisas | El dólar se debilita | Separa el efecto divisa del efecto bolsa | Panel |
| Impacto del mundo | Materias primas o geopolítica | Sube el petróleo | Efecto neto: lo que gana una parte de la cartera y pierde otra | Panel |
| Impacto del mundo | Agenda de la semana | "¿Qué viene que me afecte?" | Próximos eventos con el % de la cartera expuesto | Panel, resumen semanal |
| Prevenir | Concentración oculta | Las mismas empresas en varios fondos | Detecta el solapamiento y lo cuantifica | Panel, aviso |
| Prevenir | Desviación del plan | Renta variable al 76% frente al 70% objetivo | Estado "Revisa tu plan" | Widget, aviso |
| Prevenir | Reacción impulsiva en caídas | "Ha caído todo, ¿vendo?" | Contexto histórico e impacto en su objetivo; nunca una orden | Voz |
| Prevenir | Prueba de estrés | "¿Y si la bolsa cae un 20%?" | Escenarios en euros por activo | Panel, voz |
| Oportunidad según el plan | Reequilibrar sin vender | Se ha desviado de su 70/30 | Muestra la opción de dirigir las aportaciones al activo que falta, según su propia regla | Panel |
| Oportunidad según el plan | Aprovechar las caídas con el DCA | El mercado baja antes de su aportación | "Tu aportación de este mes compra más barato" | Aviso, panel |
| Oportunidad según el plan | Mover dinero sin pagar impuestos | Quiere cambiar de fondo | Indica qué posiciones admiten traspaso sin tributar | App |
| Gestionar | Registrar una operación | Ha comprado en su bróker | Comprar, vender y traspasar al precio del momento | App |
| Gestionar | Aportar cada mes | 300 € al mes, 70/30 | Plan DCA con registro y recordatorio | App |
| Planificar | Saber si llega a su objetivo | "¿Llego a 2040?" | Proyección con el DCA y escenarios pesimistas | Voz, panel |

Fuera de foco en el MVP: el inversor avanzado que opera a diario y el principiante sin ninguna inversión todavía.

## Propuesta de valor y principios

KAIROS no te dice qué comprar: te dice qué tienes, cómo te afecta lo que pasa en el mundo y si tu plan sigue en pie. Centraliza la información financiera del mundo y la filtra por tu perfil.

**Principios de producto** (criterio para decidir cada feature)

1. **Personalización total.** La misma noticia produce un mensaje distinto para cada cartera. Si un evento no toca tu cartera, no lo ves.
2. **Menos es más.** Una cifra y una frase en pantalla. Si algo no cabe en el widget o en una respuesta de voz de 20 segundos, va al panel, no a la portada.
3. **Siempre en euros de tu cartera.** Nunca "el mercado cae un 2%", sino "tu cartera pierde 640 €".
4. **Contexto, no órdenes.** Nunca "compra" ni "vende". Los riesgos y oportunidades se expresan siempre frente a las reglas que el propio usuario se ha fijado.
5. **Calmar antes que alarmar.** El silencio también es información: si no hay aviso, no hay nada que hacer. Máximo 1-2 avisos por semana.
6. **Todo es verificable.** Cada cifra tiene detrás un cálculo y una fuente que se pueden consultar.
7. **Por dentro complejo, por fuera simple.** Los agentes, el look-through y el motor de impacto existen, pero el usuario no los ve.

## Experiencia de usuario

La experiencia tiene cuatro piezas de menos a más detalle: un widget, una pregunta por voz, un aviso solo cuando importa y un panel de contexto para quien quiera profundizar.

### 1. Widget: una cifra y una frase

> **42.380 €** · −1,2% esta semana "Movimiento normal. Tu plan sigue en pie."

| Estado | Cuándo | Frase de ejemplo |
| --- | --- | --- |
| Tranquilo | Todo dentro de lo normal (la mayoría de los días) | "Movimiento normal. Tu plan sigue en pie." |
| Atento | Un evento relevante afecta a la cartera | "Tus fondos tecnológicos caen tras resultados. Toca para ver por qué." |
| Revisa tu plan | Desviación de la asignación que el usuario se marcó | "Tu renta variable es el 82% (tu objetivo: 70%)." |

Cada estado lleva color y palabra, para que se entienda sin depender del color.

### 2. Voz: pulsas y preguntas

Tres preguntas cubren casi todo el uso; la respuesta dura 15-20 segundos y siempre incluye una cifra en euros.

- **"¿Por qué ha bajado?"** → "Sobre todo por tu fondo tecnológico: las grandes tecnológicas de EE. UU. han caído tras sus resultados. Te ha restado unos 500 euros."
- **"¿Me afecta lo del BCE?"** → "Poco. Tus fondos de renta fija suben ligeramente; en total, unos 90 euros a tu favor."
- **"¿Voy bien?"** → "Sí. Para tu objetivo de 2040 vas en línea. Sigue con tus aportaciones de siempre."

### 3. Avisos: solo cuando importa

- Como máximo 1-2 notificaciones por semana, solo por encima de un umbral de impacto en euros.
- Resumen en audio de 30 segundos los domingos, como un podcast de tu cartera.
- Sin dashboard de gráficos, sin chat largo y sin noticias en bruto: el usuario ve lo que significan para él, no los titulares.

### 4. Panel de contexto: el mundo, traducido a tu cartera

El panel (web y tableta) reúne en una pantalla todo el contexto de la cartera y del mundo, ya filtrado por el perfil del usuario. Bloques:

| Bloque | Qué muestra |
| --- | --- |
| Resumen | Patrimonio, impacto de los eventos de hoy con su rango, número de riesgos y oportunidades, exposición dominante |
| El mundo, traducido a tu cartera | Cada evento con su cadena causal (evento → canal → tu activo), impacto en €, rango, confianza y qué significa para ti; filtrable por riesgo, oportunidad o neutral |
| Tu exposición real | Región, sector, divisa y empresas repetidas, mirando dentro de los fondos |
| ¿Y si…? | Escenarios (bolsa −10%, tipos, dólar, petróleo) con el impacto desglosado por activo |
| Riesgos y oportunidades según tu plan | Concentración, divisa y desviación del plan; reequilibrio, aportación más barata y traspasos sin tributar |
| Próximos eventos | Agenda (BCE, resultados, inflación, tu aportación) con el % de la cartera expuesto |

## Cartera, aportaciones y operaciones

La cartera vive dentro de KAIROS: el usuario la da de alta al descargar la app, define sus aportaciones periódicas y registra compras, ventas y traspasos, y los precios se actualizan con el mercado.

### 1. Alta de la cartera

- Por cada activo, el usuario indica tres datos: ISIN o ticker, número de participaciones y precio medio de compra.
- KAIROS completa el resto: tipo (fondo, ETF, acción, depósito), divisa, categoría, comisiones (TER), composición para el look-through y si admite traspaso.
- Desde el primer minuto el usuario ve la distribución de su cartera y su valor actual.

### 2. Plan de aportaciones periódicas (DCA)

- El usuario define importe, frecuencia, día y reparto por activo. Ejemplo: 300 € al mes, el día 5, 70% a un fondo MSCI World y 30% a un fondo de renta fija.
- El día que toca, KAIROS registra la compra al precio de ese día y actualiza las participaciones; un aviso permite confirmarla o saltarla.
- Admite varios planes a la vez, que se pueden pausar o editar.
- El motor usa el DCA para proyectar la cartera futura cuando el usuario pregunta "¿voy bien?".

### 3. Operaciones manuales

| Operación | Qué hace en KAIROS | Precio usado | Reglas |
| --- | --- | --- | --- |
| Comprar | Suma participaciones y recalcula el precio medio | Último precio disponible | Por importe en € o por número de participaciones |
| Vender | Resta participaciones y calcula la plusvalía o minusvalía estimada | Último precio disponible | No más participaciones de las que se tienen; método FIFO |
| Traspasar | Mueve el valor de un fondo a otro conservando el coste y la fecha de compra, sin tributar | Valor liquidativo de ambos fondos | Solo de fondo a fondo; los ETF y las acciones no admiten traspaso ([GuiaFiscal](https://guiafiscal.es/inversiones/etf-fiscalidad-2026-guia/), [AllInvestView](https://www.allinvestview.com/es/traspaso-fondos-inversion/)): la app lo explica y ofrece vender y comprar con aviso fiscal |

Las operaciones son registros en KAIROS, no órdenes reales: el usuario las ejecuta en su banco o bróker. Así KAIROS no necesita licencia de intermediario y mantiene el principio de "contexto, no órdenes". Con los conectores (F14), las posiciones reales se sincronizarían solas.

### 4. Precios en tiempo real

- **Acciones y ETFs:** cotización durante la sesión, refrescada cada minuto aproximadamente. Con las capas gratuitas de las APIs de mercado los precios pueden llegar con unos minutos de retraso; la app muestra la hora de cada precio.
- **Fondos de inversión:** un valor liquidativo al día; la app muestra "VL a fecha X".
- **Divisas:** todo se convierte a euros con el tipo de cambio del momento.
- El widget y el motor de impacto usan siempre el último precio disponible.

### 5. Modelo de datos

| Entidad | Campos clave |
| --- | --- |
| Activo | ISIN o ticker, nombre, tipo, divisa, categoría, TER, traspasable (sí/no), composición |
| Posición | Activo, participaciones, precio medio, fecha de la primera compra |
| Operación | Tipo (compra, venta, traspaso, aportación DCA), fecha, participaciones, precio, activo de origen y destino |
| Plan DCA | Importe, frecuencia, día, reparto por activo, estado (activo o pausado) |
| Precio | Activo, valor, fecha y hora, fuente |

## Features

El MVP del hackathon son 12 features que bastan para la demo; el resto se decide según el tiempo. Cambiad la prioridad en la última columna.

| # | Feature | Qué hace | Módulo | Prioridad |
| --- | --- | --- | --- | --- |
| F1 | Alta de cartera | Al descargar la app: activos por ISIN o ticker, participaciones, precio medio y perfil; características autocompletadas | Cartera | MVP hackathon |
| F2 | Precios en tiempo real | Acciones y ETFs intradía; fondos con su valor liquidativo diario; todo en euros | Precios | MVP hackathon |
| F3 | Look-through de fondos | Composición de ETFs y fondos → exposición por país, sector, divisa y empresa | Exposición | MVP hackathon |
| F4 | Operaciones manuales | Comprar, vender y traspasar al precio del momento; recalcula participaciones y precio medio | Cartera | MVP hackathon |
| F5 | Plan DCA | Importe, frecuencia y reparto por activo; registra cada aportación al precio del día | Cartera | MVP hackathon |
| F6 | Widget de estado | Cifra + frase + estado (Tranquilo / Atento / Revisa tu plan) | App | MVP hackathon |
| F7 | Pregunta por voz | Mantener pulsado, preguntar, respuesta hablada de 15-20 s | Voz + agente | MVP hackathon |
| F8 | Motor de impacto | Betas por factor (mercado, tipos, petróleo, EUR/USD) → impacto en € con rango | Motor | MVP hackathon |
| F9 | Eventos en modo replay | Reproduce 3 tipos de evento reales pasados: BCE, petróleo, resultados | Eventos | MVP hackathon |
| F10 | Agente guardián | Revisa cada respuesta: sin órdenes de compraventa, con fuentes | Cumplimiento | MVP hackathon |
| F23 | Panel de contexto | El mundo traducido a tu cartera: eventos con cadena causal, impacto en €, exposición real y agenda | App (web) | MVP hackathon |
| F24 | Radar de riesgos y oportunidades | Concentración, divisa y desviación; oportunidades siempre frente a las reglas del usuario | Exposición + plan | MVP hackathon |
| F25 | Escenarios ¿Y si…? | Bolsa, tipos, dólar, petróleo: impacto en € desglosado por activo | Motor | Si da tiempo |
| F11 | Plan del usuario | Asignación objetivo y meta; aviso si se desvía; proyección con el DCA | Plan | Si da tiempo |
| F12 | Notificación push | Aviso solo por encima de un umbral de impacto en €; recordatorio del DCA | Avisos | Si da tiempo |
| F13 | Radiografía de cartera | "Crees que tienes 3 fondos, pero el 61% está en EE. UU." | Exposición | Si da tiempo |
| F14 | Conectores de brókers | Sincronizar posiciones por API o MCP (Trading 212 en demo) y cuentas por open banking (sandbox) | Cartera | Si da tiempo |
| F15 | Resumen semanal en audio | 30 s cada domingo | Avisos + voz | Después |
| F16 | Eventos en vivo | Noticias reales en tiempo real en lugar de replay | Eventos | Después |
| F17 | Historial de aciertos | Impacto estimado frente al real a los 5 días | Motor | Después |
| F18 | Widget nativo y asistente del sistema | WidgetKit / Jetpack Glance, Siri / Google Assistant | App | Después |
| F19 | KAIROS como servidor MCP | Preguntar por tu cartera desde Claude o ChatGPT | Integraciones | Después |
| F20 | Recomendaciones de compraventa | Decir qué comprar o vender | — | Descartado |
| F21 | Dashboard recargado en la portada | Gráficos detallados como pantalla principal del móvil (el detalle vive en el panel) | — | Descartado |
| F22 | Ejecutar órdenes en el bróker | Enviar órdenes reales o mover dinero | — | Descartado |

F20 se descarta por regulación (MiFID II); F21 y F22, por el principio de menos es más y por seguridad. Las operaciones de F4 y F5 son registros en KAIROS, no órdenes reales.

## Alcance del MVP y demo

El MVP es una web móvil (widget, voz y app) más un panel web de contexto, sobre una cartera de ejemplo y eventos reales reproducidos.

**Dentro del alcance**

- Alta manual de una cartera de 6-8 posiciones (2-3 ETFs o fondos con su composición) y del perfil, con una cartera de ejemplo precargada para la demo.
- Un plan DCA y las tres operaciones manuales: comprar, vender y traspasar.
- Precios en tiempo real para acciones y ETFs y valor liquidativo diario para fondos.
- 3 tipos de evento en modo replay: decisión del BCE, movimiento del petróleo y resultados de una empresa, cada uno con su cadena causal.
- Widget simulado en una pantalla de inicio de móvil (web responsive).
- Voz: mantener pulsado → transcripción → agente → respuesta hablada.
- Panel de contexto web: eventos traducidos a la cartera, exposición real y radar de riesgos y oportunidades.
- Motor de impacto con betas calculadas sobre 2-3 años de precios diarios.
- Agente guardián activo en todas las respuestas.

**Fuera del alcance**

- Conexión directa con bancos (open banking) y cualquier operación con dinero.
- Noticias en tiempo real: se usa replay para que la demo no dependa de que "pase algo".
- Widget nativo de iOS/Android, salvo que alguien domine Kotlin (Jetpack Glance).
- Varios perfiles de usuario, login real y niveles principiante/avanzado.

**Guion de demo (3 minutos)**

1. Alta de la cartera en menos de un minuto (o cartera de ejemplo) → aparece la distribución y el widget en estado Tranquilo, con precios moviéndose en directo.
2. Radiografía: "Crees que tienes 3 fondos distintos, pero el 61% de tu dinero está en EE. UU. y el 19% en 7 empresas."
3. Replay de un evento real → el widget pasa a Atento y llega el aviso con el impacto en euros.
4. Pregunta en voz alta delante del jurado: "¿Por qué ha bajado?" → responde en 15-20 segundos con la cadena causal.
5. Abrir el panel: el mismo día, todos los eventos traducidos a la cartera, con sus riesgos y oportunidades según el plan.
6. Golpe final de personalización: la misma noticia en la cartera de Laura y en la de Javier, con mensajes distintos.
7. "¿Voy bien?" → proyección con el DCA frente al objetivo: "Tu plan sigue en pie."
8. Cierre: pantalla con el cálculo y las fuentes detrás de cada cifra (trazabilidad).

## Arquitectura

Tres agentes de IA entienden y explican; el gestor de cartera y el motor de impacto, ambos deterministas, calculan todas las cifras.

&#91;embedded content: arquitectura del MVP · 3 fuentes, 5 componentes de backend, 3 piezas de app\]

La cartera llega al motor desde el gestor de cartera y las noticias desde el agente de eventos; el explicador redacta la respuesta y el guardián la revisa antes de que llegue al móvil. Las preguntas por voz entran directamente al explicador.

**Herramientas del agente explicador** (tool calling)

- `get_portfolio`: posiciones y valor actual.
- `get_exposure`: exposición por país, sector, empresa y divisa (look-through).
- `get_events`: eventos recientes que afectan a la cartera.
- `estimate_impact`: impacto en € con rango y confianza, desde el motor.
- `check_plan`: desviación frente a la asignación objetivo del usuario.

**Stack propuesto**

| Capa | Tecnología | Nota |
| --- | --- | --- |
| App | React + TypeScript (web móvil) | Simula el widget; nativo con WidgetKit / Jetpack Glance después |
| Backend | Python + FastAPI | API y orquestación de agentes |
| Agentes | Claude (API de Anthropic) con tool calling y salida estructurada (JSON) | Modelo rápido (Haiku) para voz y avisos; modelo potente (Sonnet/Opus) para analizar eventos, que se hace por adelantado. Caché de prompts con el contexto de la cartera |
| Motor | Python: pandas, statsmodels | Betas por factor y escenarios |
| Voz | ElevenLabs: Scribe v2 Realtime (voz a texto, <150 ms) + Flash v2.5 (texto a voz, \~75 ms). Alternativa: ElevenLabs Agents con Claude como LLM | Respuestas de 2-3 frases, en streaming; voz clara y pausada para mayores |
| Datos | PostgreSQL + caché de APIs | Dataset de respaldo para la demo |
| Despliegue | Docker Compose | — |

## Datos y fuentes

Todo el MVP puede funcionar con capas gratuitas y datos públicos, con un dataset cacheado de respaldo para la demo.

| Necesidad | Fuente candidata | Nota |
| --- | --- | --- |
| Noticias por empresa | Finnhub, Marketaux ([comparativa](https://qveris.ai/guides/best-free-financial-news-api/)) | Finnhub: licencia gratuita para uso personal, sentimiento de pago ([QVeris](https://api.qveris.ai/guides/best-free-financial-news-api)) |
| Noticias + sentimiento | Alpha Vantage | Capa gratuita de unas 25 peticiones al día ([API Cost Calc](https://apicostcalc.com/alpha-vantage.html)): cachear |
| Eventos globales | GDELT | Abierto |
| Hechos relevantes de cotizadas | CNMV (otra información relevante) | Público |
| Calendario macro (BCE, IPC) y consenso | Calendario del BCE + fuente de previsiones | Para medir la sorpresa frente a lo esperado |
| Precios históricos | Alpha Vantage, Twelve Data o similar | Para calcular betas |
| Composición de ETFs y fondos | Ficheros de posiciones de las gestoras; informes semestrales en la CNMV | Base del look-through |
| Cartera del usuario | Alta manual en la app (cartera de ejemplo en la demo); conectores de brókers como mejora (F14) | Sin contraseñas |

Pregunta abierta: qué fuente de previsiones de consenso usar para medir la sorpresa de los datos macro.

## Regulación, riesgos y ética

El mayor riesgo es cruzar la línea del asesoramiento regulado; el producto se diseña para no hacerlo.

| Riesgo | Por qué importa | Mitigación |
| --- | --- | --- |
| Asesoramiento sin licencia (MiFID II) | Una recomendación personalizada de inversión es un servicio regulado; ESMA pide cumplir MiFID II cuando la IA asesora o gestiona carteras ([Paperjam](https://en.paperjam.lu/article/esma-issues-guidance-on-ai-use)) | Nunca "compra" ni "vende"; solo información e impacto; reglas fijadas por el propio usuario; agente guardián + aviso "no es asesoramiento" |
| Transparencia de la IA (AI Act, art. 50) | Obligatorio informar de que se habla con una IA desde agosto de 2026 | Aviso visible en la app y al inicio de la voz |
| Alucinaciones en cifras | Una cifra inventada destruye la confianza | El LLM nunca calcula: los números salen del motor determinista y se muestran con su fuente |
| Estimaciones imprecisas | Las betas cambian con el tiempo | Rangos con confianza, nunca una cifra exacta; historial de aciertos (F13) |
| Empujar a operar | Más avisos → más operaciones a destiempo | Máximo 1-2 avisos por semana; mensajes orientados a calmar y contextualizar |
| Datos personales (RGPD) | Datos financieros sensibles | Sin credenciales bancarias; minimización; consentimiento; cartera de ejemplo en la demo |
| Límites y licencias de APIs | Las capas gratuitas tienen cuotas bajas y uso personal | Caché y dataset de respaldo; revisar licencias antes de producto |
| El mercado ya descontó la noticia | No hay ventaja para operar | Posicionar como comprensión y gestión del riesgo, no como señal de trading |

## Modelo de negocio y viabilidad

La rúbrica pide que el proyecto sea viable financieramente. KAIROS tiene dos vías; la principal es la primera.

| Vía | Cliente | Cómo cobra | Por qué tiene sentido |
| --- | --- | --- | --- |
| B2B2C (principal) | Brókers, neobancos y gestoras de fondos indexados (por ejemplo, MyInvestor) | Licencia de marca blanca por usuario activo al mes | Al bróker le interesa que el cliente no venda en pánico y siga aportando: KAIROS reduce reembolsos y aumenta las aportaciones. Además, el bróker ya tiene la cartera, así que desaparece el problema de conectar datos |
| B2C freemium | Inversor particular | Gratis: widget y 1-2 avisos por semana. De pago: voz sin límite, escenarios y panel completo | Valida el producto y crea demanda antes de vender a entidades |

**Costes por usuario.** Lo caro (analizar cada evento con el modelo potente) se hace una vez por evento y sirve para todos los usuarios; por usuario solo se calcula el impacto (determinista, casi gratis) y se generan frases cortas con el modelo rápido. La voz solo se paga cuando el usuario habla. Antes del pitch hay que poner números reales a partir de los precios actuales de la API de Claude y de ElevenLabs.

**Contexto de mercado.** GPTadvisor (wealthtech B2B) ya ofrece a entidades «sube tu cartera y habla con una IA», ha trabajado con Indexa y tiene una alianza con MyInvestor para llevar sus herramientas a asistentes como ChatGPT o Claude. Eso confirma que hay demanda en España y que las entidades pagan por esto. También marca la diferencia que hay que defender: GPTadvisor responde cuando preguntas; KAIROS **avisa sin que preguntes**, en euros, con look-through de fondos y por voz.

## Competencia y diferencial

La idea está validada: en 2026 Perplexity, OpenAI y Robinhood conectan carteras a una IA, pero en EE. UU. y para acciones. En Europa, donde se invierte sobre todo en fondos, nadie traduce el mundo a tu cartera. Ripplora es el competidor más parecido y hay que diferenciarse de él punto por punto.

| Competidor | Qué hace | Hueco que deja |
| --- | --- | --- |
| [Ripplora](https://www.producthunt.com/p/ripplora) | Impacto de eventos macro (IPC, Fed, empleo) en tus acciones y ETFs, con riesgo y rangos; importación CSV/PDF; chat; alertas | Terminal para operar, centrado en EE. UU. y en acciones y ETFs; sin fondos por dentro |
| [Perplexity Portfolio](https://truthifi.com/education/perplexity-finance-vs-truthifi) | Conecta brókers vía Plaid y responde con noticias sobre tus posiciones | Solo EE. UU. y Canadá; responde si preguntas, no se anticipa |
| ChatGPT Finances | Conecta cuentas y analiza gastos, suscripciones e inversiones | Solo EE. UU.; asistente general, sin motor de impacto |
| [Robinhood Cortex Digests](https://robinhood.com/us/en/support/articles/cortex-digests) | Resúmenes con IA de lo que afecta a tu cartera | Solo EE. UU. y solo su cuenta |
| [Google Finance](https://thenextweb.com/news/google-finance-android-app-portfolios-ai-research-tool?type=News) | Carteras y resúmenes programados con IA | Acciones; no mira dentro de los fondos ni calcula en euros |
| [Lightyear](https://lightyear.com/en-ee/blog/ai-powered-market-intelligence-for-every-investor) | Resúmenes de noticias cuando un valor se mueve; sobreexposición | Solo lo que tienes en Lightyear |
| [Montrose](https://allmind.ai/news/01c6cdd04eb7ee7c2c0437577a46b3591d49821913c8a47b0c2220fc808e9da6) | Conecta tu cartera de acciones y fondos a tu propia IA | Solo clientes de Montrose; la IA la pone el usuario |
| getquin, Finary | Agregadores de patrimonio con análisis por IA | Foto de la cartera, sin traducción de eventos a euros |
| Morningstar X-Ray, Finect | Look-through y solapamiento de fondos | Informe estático, sin noticias ni impacto |
| Apps de bancos y brókers españoles | Asistentes sobre sus propios productos | Solo ven su entidad y tienen producto que vender |

**KAIROS frente a Ripplora**

| Dimensión | Ripplora | KAIROS |
| --- | --- | --- |
| Para quién | Inversor activo que opera ("antes de operar") | Inversor a largo plazo que no quiere vivir pendiente del mercado |
| Activos | Acciones y ETFs | Fondos, ETFs, acciones y planes de pensiones, mirando dentro de cada fondo |
| Eventos | Macro de EE. UU. (IPC, Fed, empleo) | BCE, Europa y EE. UU., resultados de empresas aunque estén dentro de un fondo, divisas |
| Explicación | Puntuación de riesgo y rango de impacto | Cadena causal (evento → canal → tu activo) + euros con rango + qué significa para ti |
| Personalización | Según tus posiciones | Según tus posiciones, tu perfil, tu objetivo y tu plan de aportaciones |
| Oportunidades | Escaneo de oportunidades de mercado | Solo frente a tus propias reglas (reequilibrio, DCA, traspasos), compatible con MiFID II |
| Interfaz | Terminal con datos | Widget + voz; panel solo para profundizar |
| Fiscalidad española | No | Traspasos sin tributar, FIFO, valor liquidativo |
| Idioma y mercado | Inglés, EE. UU. | Español, España y Europa |

**Qué mejoramos frente a Ripplora**

1. **Mirar dentro de los fondos.** Avisar de una noticia aunque la empresa no esté en tu cartera directamente, sino dentro de tu fondo indexado.
2. **Explicar el porqué, no solo puntuar.** Cadena causal visible y frase en lenguaje llano, adaptada al perfil.
3. **Historial de aciertos público.** Comparar el impacto estimado con el real a los 5 días y enseñarlo: confianza medible.
4. **Separar efectos.** Distinguir cuánto se debe a la bolsa y cuánto al tipo de cambio.
5. **Del evento al plan.** Cada evento se cruza con el objetivo y el DCA del usuario: "¿sigo bien para 2040?".
6. **Diseño conductual.** Menos avisos, mejor elegidos, y orientados a no operar por impulso.
7. **Voz y widget.** Consultar la cartera en 15 segundos sin abrir un terminal.

## Métricas, preguntas abiertas y próximos pasos

El éxito se mide por la calidad de cada aviso y por que el usuario entienda su cartera sin operar más.

**Métricas**

- Precisión del impacto: diferencia entre el impacto estimado y el real a los 5 días.
- Precisión de los avisos: avisos útiles / avisos enviados (valoración del usuario).
- Latencia de la voz: segundos desde que el usuario suelta el botón hasta que empieza la respuesta.
- Cero salidas bloqueadas por el guardián que lleguen al usuario.
- En producto real: menos operaciones impulsivas tras caídas frente a un grupo de control.

**Preguntas abiertas**

- [ ] Nombre definitivo: KAIROS (decidido).
- [ ] Criterios de evaluación y duración del hackathon.
- [ ] ¿Widget nativo Android o simulado en web?
- [ ] Proveedor de LLM y de voz (coste y latencia).
- [ ] Qué 3 eventos reales usar en el modo replay.
- [ ] Modelo de negocio para el pitch: freemium o B2B (neobancos, brókers, asesores independientes).

**Próximos pasos**

- [ ] Cerrar las features del MVP en la tabla de Features.
- [ ] Reparto de tareas: ingesta y look-through, motor de impacto, agentes y voz, app y widget.
- [ ] Preparar la cartera de ejemplo y los datos del replay.
- [ ] Ensayar la demo de 3 minutos y el pitch de 30 segundos.
