# Diseño técnico del MVP — KAIROS

Fecha: 2026-11-08 · Estado: **borrador para aprobación** · Plazo: Dom 8 (tarde) → Mié 11 (entrega antes de las 21:00)

Fuentes, por orden de autoridad:

1. `docs/kairos-spec.md`: producto. **No se cambia.**
2. `CLAUDE.md`: reglas de producto y de trabajo.
3. `docs/INGENIERIA.md`, `docs/SPEC.md`, `docs/decisiones.md` y `docs/TABLERO.md`: desarrollo técnico previo.

Este documento **completa y concreta** esos textos. Si contradice a `SPEC.md`, manda este documento, y tras la aprobación se corrige `SPEC.md` (§9). Si contradice a `kairos-spec.md`, el error está aquí.

Personas: **Persona 1 … Persona 5** (= P1…P5 de `TABLERO.md`). Los nombres reales los asigna el equipo.

| Persona | Rol | Carpetas |
| --- | --- | --- |
| Persona 1 | Cartera, precios, core, plan (proyección y agenda) e integración | `backend/app/{portfolio,prices,core,planning}`, `alembic/`, `docker-compose.yml`, `Makefile`, CI |
| Persona 2 | Exposición, motor de impacto, estado | `backend/app/{exposure,impact,status}`, `scripts/compute_betas.py` |
| Persona 3 | Agentes y eventos | `backend/app/{agents,events,alerts}`, `scripts/replay_event.py`, `scripts/eval_answers.py` |
| Persona 4 | Frontend | `frontend/` salvo `src/voice/` |
| Persona 5 | Voz, datos y entregables | `backend/app/voice`, `frontend/src/voice`, `data/`, `README.md`, PDF, PPT, vídeo |

Persona 1 es además **coordinadora de integración**: hace el merge final y decide en los conflictos de alcance.

---

## 1. Intención

KAIROS traduce un evento financiero real al impacto en euros sobre una cartera concreta, sin dar órdenes y con cada cifra trazable. El jurado puntúa sobre todo **implementación (30 %)** e **innovación (30 %)**: un producto acabado que se ejecuta con `docker compose up`, no el que tiene más features.

Por eso el diseño optimiza, en este orden:

1. Que el **guion de demo de 8 pasos** funcione entero el **martes 10 a las 18:00** (hito del producto, día 3).
2. Que **5 personas trabajen en paralelo sin esperarse**, gracias a contratos exactos y mocks desde el domingo.
3. Que **ningún número salga del LLM** y todos se puedan rastrear hasta una traza.

### Objetivos

- Las 12 features MVP de `kairos-spec.md`, más lo mínimo de F11 y F13 que exige el guion (§8, decisiones 7 y 8).
- Los objetivos de latencia del producto: widget < 1 s, valoración < 300 ms, primera palabra de voz < 2 s, explicación < 3 s y escenario < 500 ms.

### No objetivos

- Lo marcado como "Si da tiempo" o "Después" en el producto, salvo lo de §8.
- Datos en vivo de noticias, login, widget nativo.

### Antiobjetivos (aunque funcione, sería un fracaso)

- Que una cifra dicha o mostrada no cuadre con su traza.
- Una respuesta con "compra", "vende", "te recomiendo"…
- Que la demo dependa de la red del evento para algo que no sea Claude o ElevenLabs.
- Que Persona X edite la carpeta de Persona Y "para avanzar".

---

## 2. Arquitectura

La arquitectura de componentes de `SPEC.md` §4 se mantiene. Este diseño añade o precisa cinco cosas:

1. **Los números de un evento salen de los datos, no del LLM.** El analizador clasifica el evento, extrae entidades, elige qué canales (factores) aplican y redacta la cadena causal. Las **magnitudes** de los shocks salen del campo `observed` del JSON del replay, que son movimientos reales de ese día. `events` construye un `ShockSet` determinista con los factores que eligió el analizador. Si el analizador falla, se usan todos los factores observados. Así se cumple la regla 1 de `CLAUDE.md` sin perder la parte inteligente.
2. **Pipeline de evento orquestado por `events` (Persona 3).** Cada flecha es una llamada a `service.py`:

```mermaid
sequenceDiagram
  participant OP as POST /demo/replay/{id}
  participant EV as events (P3)
  participant AN as agents.analyzer (P3)
  participant IM as impact (P2)
  participant AG as agents.explainer + guardian (P3)
  participant ST as status (P2)
  participant AL as alerts (P3)
  OP->>EV: replay(event_id)
  EV->>AN: analyze(EventIn)
  AN-->>EV: EventAnalysis (o fallback)
  EV->>EV: build_shockset(analysis, observed) → ShockSet
  loop por cartera (laura, javier)
    EV->>IM: compute_event_impact(portfolio_id, analysis, shockset)
    IM-->>EV: EventImpactOut (explanation=null)
    EV->>AG: write_event_explanation(impact)
    AG-->>EV: texto validado o plantilla
    EV->>IM: attach_explanation(event_id, portfolio_id, text, status)
    EV->>ST: recompute(portfolio_id)
    ST->>AG: write_status_sentence(StatusFacts)
    EV->>AL: evaluate(portfolio_id, event_id)
  end
```

   Objetivo: < 10 s de punta a punta por replay (RF-11).
3. **Voz en tres tramos, uno por dueño.** Así nadie depende del código de otro para probar:
   - **STT** (Persona 5): `WS /voice/stt` devuelve la transcripción final.
   - **Respuesta** (Persona 3): el frontend llama a `POST /ask` (SSE), que devuelve frases ya validadas por el guardián.
   - **TTS** (Persona 5): por cada frase, el frontend llama a `POST /voice/tts` con `turn_id` e `index`. El backend **solo sintetiza frases aprobadas** por el guardián, que busca en una caché en memoria por `turn_id`, nunca texto libre del cliente. Esto aplica la regla 3 también al audio.
   - El aviso de IA del inicio de la voz es un audio pregenerado (`GET /voice/disclaimer`). Suena mientras Claude genera la primera frase y ayuda a cumplir los < 2 s.
4. **Actualización en el frontend por polling.** `/status` y `/alerts` se consultan cada 5 s. Es más simple que SSE de servidor y basta para la demo. SSE se usa solo en `/ask`.
5. **Dos endpoints nuevos:**
   - `GET /portfolios/{id}/agenda` (Persona 1, decisión 15): bloque "Próximos eventos" del panel, F23 MVP.
   - `GET /portfolios/{id}/move?period=week` (Persona 2): atribución de "¿Por qué ha bajado?". Es la herramienta `explain_move`, que antes no tenía endpoint.

Presupuesto de latencia de voz, medido desde que se suelta el botón:

| Tramo | Tiempo |
| --- | --- |
| STT final | ~300 ms |
| Primera frase de Claude rápido (contexto en caché, sin herramientas) | ~700–900 ms |
| Guardián | < 20 ms |
| TTS primer byte | ~300 ms |
| **Total** | **≈ 1,5 s** |

El disclaimer pregenerado cubre la primera vez de la sesión.

---

## 3. Convenciones de todos los contratos

| Tema | Regla |
| --- | --- |
| Importes | `Decimal` serializado como **string**, 2 decimales: `"40123.45"`. Moneda implícita EUR salvo `price_currency` |
| Participaciones y precios | String con hasta 8 decimales: `"152.30451200"` |
| Pesos, porcentajes, variaciones | **Fracción** como string: `"0.76"` = 76 %, `"-0.012"` = −1,2 %. Nunca "puntos porcentuales" en JSON |
| Shock de tipos (`RATES_EUR`) | Variación absoluta de la rentabilidad como fracción: `"-0.0010"` = −10 pb. Las betas de tipos se estiman en la misma unidad |
| Fechas | ISO 8601 en UTC con `Z`. Siempre de `core.clock.now()` |
| IDs | Cartera: `"laura"`, `"javier"`. Activo: ISIN (fondos/ETF) o ticker (acciones). Evento: slug (`"bce-2025-06"`). Traza: `"calc_"` + uuid4 hex |
| Enums | En inglés y minúsculas en el código. Los textos visibles van aparte (`*_label`, en español) |
| Errores | HTTP 4xx/5xx con `{"code": "...", "message": "texto en español", "details": {...}}` |
| Trazabilidad | Toda respuesta con cifras lleva `calc_id`. Las cifras derivadas de varias trazas llevan `parent_calc_ids` en su traza |
| Ejemplos | Cada esquema tiene un JSON en `backend/app/schemas/examples/<Modelo>.json`. Un test valida cada ejemplo contra su modelo Pydantic. Esos ejemplos **son** los mocks del backend (`mock.py` los carga) y del frontend (`make gen-api` los copia a `frontend/src/api/mocks/`). Llevan `"illustrative": true` |

Códigos de error (`core/errors.py`):

- `VALIDATION_ERROR`
- `NOT_FOUND`
- `INSUFFICIENT_UNITS`
- `TRANSFER_NOT_ALLOWED`
- `PRICE_UNAVAILABLE`
- `DCA_ALLOCATION_INVALID`
- `DEMO_MODE_DISABLED`
- `UPSTREAM_UNAVAILABLE` (Claude o ElevenLabs caídos)
- `SENTENCE_NOT_APPROVED` (TTS)

`SourceRef`, común a todos:

```json
{"kind": "price", "label": "VL iShares Core MSCI World", "ref": "IE00B4L5Y983", "as_of": "2026-11-06T00:00:00Z", "url": null}
```

Los valores posibles de `kind` son `price`, `fx`, `composition`, `beta`, `event`, `assumption` y `user_input`.

---

## 4. Contratos

Todas las cifras de los ejemplos son ilustrativas.

### 4.1 Gestor de cartera (Persona 1) → motor, agentes y app

**Interfaz Python** (`portfolio/service.py`), lo único que importan otros módulos:

```python
def get_valued(portfolio_id: str) -> PortfolioOut
def get_plan(portfolio_id: str) -> PlanOut
def list_dca_plans(portfolio_id: str) -> list[DcaPlanOut]
def get_value_change(portfolio_id: str, start: datetime, end: datetime) -> ValueChangeOut
def list_portfolio_ids() -> list[str]
# prices/service.py
def latest(asset_id: str) -> PriceOut
def fx_rate(pair: str, at: datetime | None = None) -> Decimal
def history(asset_id: str, start: date, end: date) -> list[PriceOut]
# core/trace.py
def record(kind: str, formula: str, inputs: dict, outputs: dict,
           sources: list[SourceRef], parent_calc_ids: list[str] = []) -> str  # calc_id
```

**`PortfolioOut`**: `GET /portfolios/{id}`.

```json
{
  "id": "laura",
  "name": "Laura",
  "profile": "dinamico",
  "total_eur": "42380.00",
  "change_week_eur": "-514.00",
  "change_week_pct": "-0.012",
  "allocation": {"equity": "0.76", "fixed_income": "0.24", "cash": "0.00", "mixed": "0.00"},
  "positions": [
    {
      "asset_id": "IE00B4L5Y983",
      "isin": "IE00B4L5Y983",
      "ticker": "IWDA",
      "name": "iShares Core MSCI World",
      "asset_type": "etf",
      "asset_class": "equity",
      "units": "152.30451200",
      "avg_cost_eur": "78.10",
      "price": "95.42000000",
      "price_currency": "EUR",
      "price_at": "2026-11-06T16:35:00Z",
      "price_kind": "intraday",
      "fx_rate": "1",
      "value_eur": "14532.85",
      "weight": "0.343",
      "unrealized_pnl_eur": "2637.00",
      "transferable": false,
      "first_acquired_at": "2023-03-05T00:00:00Z"
    }
  ],
  "demo_adjustments": [{"event_id": "nvda-2025-02", "impact_eur": "-470.00", "label": "Estimación tras el evento", "calc_id": "calc_..."}],
  "valued_at": "2026-11-08T18:00:00Z",
  "calc_id": "calc_3f1e..."
}
```

`demo_adjustments` (decisión 17) solo tiene elementos con `DEMO_MODE=true` tras un replay. `total_eur`, `change_week_*` y cada `value_eur` **ya los incluyen**: cada posición suma su `impact_eur` del `breakdown` del evento. La lista va vacía fuera de demo. El frontend muestra la etiqueta junto al patrimonio cuando la lista no está vacía.

Valores de los enums:

- `asset_type`: `fund`, `etf`, `stock`, `deposit`, `pension_plan`.
- `asset_class`: `equity`, `fixed_income`, `cash`, `mixed`.
- `price_kind`: `intraday`, `nav_daily`.
- `profile`: `conservador`, `moderado`, `dinamico`.

**`PlanOut`**: `GET/PUT /portfolios/{id}/plan`.

```json
{
  "portfolio_id": "laura",
  "target": {"equity": "0.70", "fixed_income": "0.30", "cash": "0.00"},
  "drift_threshold": "0.10",
  "goal_amount_eur": "150000.00",
  "goal_year": 2040,
  "current": {"equity": "0.76", "fixed_income": "0.24", "cash": "0.00"},
  "drift_equity": "0.06",
  "drift_exceeded": false,
  "calc_id": "calc_..."
}
```

**Operaciones**: `POST /portfolios/{id}/transactions`.

```json
// request: compra por importe (o "units": "3.5" en vez de amount_eur; exactamente uno de los dos)
{"type": "buy", "asset_id": "IE00B4L5Y983", "amount_eur": "300.00"}
// request: venta
{"type": "sell", "asset_id": "US0378331005", "units": "5"}
```

```json
// response 201
{
  "transaction_id": "tx_...",
  "type": "sell",
  "asset_id": "US0378331005",
  "units": "5.00000000",
  "price": "228.10000000", "price_currency": "USD", "price_at": "2026-11-06T21:00:00Z", "fx_rate": "0.8621",
  "amount_eur": "983.21",
  "effect": {
    "units_after": "10.00000000",
    "avg_cost_eur_after": "151.20",
    "realized_gain_eur": "227.10",
    "lots_consumed": [{"lot_id": "lot_...", "acquired_at": "2023-05-02T00:00:00Z", "units": "5.00000000", "cost_eur_per_unit": "151.20"}]
  },
  "portfolio": { "...": "PortfolioOut" },
  "calc_id": "calc_..."
}
```

**Traspaso**: `POST /portfolios/{id}/transfers`.

```json
// request ("units" o "amount_eur", exactamente uno)
{"from_asset_id": "ES0165151004", "to_asset_id": "IE00BYX5MX67", "units": "120"}
```

```json
// 422 si alguno de los dos no es fund
{"code": "TRANSFER_NOT_ALLOWED",
 "message": "Los ETF y las acciones no admiten traspaso sin tributar. Puedes registrar una venta y una compra; la venta tributa.",
 "details": {"from_asset_type": "etf", "to_asset_type": "fund", "alternative": "sell_and_buy", "estimated_gain_eur": "412.00"}}
```

La respuesta 201 tiene la misma forma que la de una operación. En `effect` va `lots_created` (con `acquired_at` y el coste total conservados) en lugar de `realized_gain_eur`.

**DCA**: `GET/POST/PATCH /portfolios/{id}/dca-plans`, `POST /dca-executions/{id}`.

```json
// DcaPlanOut
{"id": "dca_1", "portfolio_id": "laura", "amount_eur": "300.00", "frequency": "monthly", "day": 5,
 "status": "active", "allocations": [{"asset_id": "IE00B4L5Y983", "weight": "0.70"}, {"asset_id": "IE00BYX5MX67", "weight": "0.30"}],
 "last_execution_at": "2026-10-05T00:00:00Z", "next_execution_at": "2026-11-05T00:00:00Z"}
// DcaExecutionOut (POST /demo/dca/run crea una "pending")
{"id": "dcx_...", "dca_plan_id": "dca_1", "scheduled_for": "2026-11-05T00:00:00Z", "status": "pending",
 "lines": [{"asset_id": "IE00B4L5Y983", "amount_eur": "210.00", "price": "95.42000000", "price_at": "...", "units_estimated": "2.20079648"}]}
// POST /dca-executions/{id}   request: {"action": "confirm"} | {"action": "skip"}
```

Valores permitidos: `frequency` es `monthly` o `weekly`; `status` del plan es `active` o `paused`; `status` de la ejecución es `pending`, `confirmed` o `skipped`. Que Σ weight sea 1 se valida con tolerancia 0, porque es `Decimal`.

**`ValueChangeOut`** (solo interno, para `explain_move`):

```json
{"portfolio_id": "laura", "start": "...", "end": "...", "start_value_eur": "42894.00", "end_value_eur": "42380.00",
 "net_flows_eur": "0.00",
 "by_asset": [{"asset_id": "...", "start_value_eur": "...", "end_value_eur": "...", "flows_eur": "0.00"}],
 "calc_id": "calc_..."}
```

**`TraceOut`**: `GET /traces/{calc_id}` (Persona 1; la pantalla es de Persona 4).

```json
{"calc_id": "calc_...", "kind": "event_impact", "created_at": "...",
 "formula": "I_i = V_i · ((1 + Σ_f β_if·s_f)(1 + r_fx) − 1)",
 "inputs": {"positions": ["..."], "betas": ["..."], "shocks": {"RATES_EUR": "-0.0010"}},
 "outputs": {"impact_eur": "90.00", "low_eur": "40.00", "high_eur": "140.00"},
 "sources": [{"kind": "event", "label": "BCE 5 jun 2025", "ref": "bce-2025-06", "as_of": "...", "url": "https://..."}],
 "parent_calc_ids": ["calc_..."]}
```

Valores de `kind`: `valuation`, `transaction`, `transfer`, `dca`, `plan`, `exposure`, `event_impact`, `scenario`, `projection`, `status`, `radar`, `move` y `agenda`.

### 4.2 Analizador (Persona 3) → motor de impacto (Persona 2)

**Evento de replay** (`data/events/replay/<id>.json`, Persona 5 + Persona 3). Amplía el formato de `SPEC.md` §12: `observed` se separa en factores y empresas, y `consensus` pasa a ser un objeto con nombre.

```json
{
  "id": "bce-2025-06",
  "type": "central_bank",
  "title": "El BCE baja los tipos 0,25 puntos",
  "occurred_at": "2025-06-05T12:15:00Z",
  "text": "…comunicado o nota de prensa, en español…",
  "source_urls": ["https://www.ecb.europa.eu/..."],
  "observed": {
    "factors": {"RATES_EUR": "-0.0010", "EQ_GLOBAL": "0.0040", "EQ_US_TECH": "0.0030", "OIL": "0.0010", "EURUSD": "-0.0020"},
    "companies": {}
  },
  "observed_source": "data/prices + data/factors, cierre del día frente al cierre anterior",
  "consensus": {"metric": "rate_change_bp", "expected": "-25", "actual": "-25", "source": "…"},
  "illustrative": false
}
```

Para resultados de una empresa: `"companies": {"NVDA": "-0.085"}`. La clave es la misma `constituent_key` que en `composition`. `consensus` puede ser `null` (decisión 6 de §8).

**`EventAnalysis`**: salida del analizador, validada con Pydantic y guardada en `event.analysis`. **No contiene ningún número**: un validador rechaza dígitos en los campos de texto, salvo `title`, que viene del JSON del evento.

```json
{
  "schema_version": 1,
  "event_id": "bce-2025-06",
  "event_type": "central_bank",
  "entities": [{"kind": "central_bank", "key": "ECB", "name": "Banco Central Europeo"}],
  "channels": [
    {"factor": "RATES_EUR", "direction": "down", "label": "tipos", "rationale": "Bajada de tipos oficiales"},
    {"factor": "EQ_GLOBAL", "direction": "up", "label": "bolsa", "rationale": "Financiación más barata"}
  ],
  "companies": [],
  "causal_chain": ["El BCE baja los tipos", "Baja la rentabilidad de los bonos", "Suben de precio los fondos de renta fija"],
  "relevance": "high",
  "analyzed_model": "claude-sonnet-5-5",
  "fallback": false
}
```

Valores permitidos:

- `event_type`: `central_bank`, `commodity`, `earnings`, `fx`, `macro`.
- `entities[].kind`: `central_bank`, `company`, `commodity`, `currency`, `country`.
- `channels[].factor`: `EQ_GLOBAL`, `EQ_US_TECH`, `RATES_EUR`, `OIL`, `EURUSD`.
- `direction`: `up`, `down`.
- `companies[]`: `{"key": "NVDA", "name": "NVIDIA"}`.
- `relevance`: `high`, `medium`, `low`.

Si el analizador falla tras 1 reintento, `events` crea un análisis de respaldo: `fallback: true`, canales iguales a todas las claves de `observed.factors`, y `causal_chain` tomada de un campo `fallback_chain` del JSON del replay, que escribe un humano.

**`ShockSet`**: lo construye `events` de forma determinista y entra en el motor.

```json
{"event_id": "bce-2025-06",
 "factor_shocks": {"RATES_EUR": "-0.0010", "EQ_GLOBAL": "0.0040"},
 "company_moves": {},
 "selected_by": "analyzer",
 "source": {"kind": "event", "label": "Movimientos observados el 5 jun 2025", "ref": "bce-2025-06", "as_of": "2025-06-05T00:00:00Z", "url": null}}
```

`selected_by` vale `analyzer` o `all_observed`.

**Interfaz Python del motor** (`impact/service.py`):

```python
def compute_event_impact(portfolio_id: str, analysis: EventAnalysis, shocks: ShockSet) -> EventImpactOut
def attach_explanation(event_id: str, portfolio_id: str, text: str, status: ExplanationStatus) -> None
def estimate_scenario(portfolio_id: str, shocks: dict[Factor, Decimal]) -> ScenarioOut
def list_event_impacts(portfolio_id: str, days: int) -> list[EventImpactOut]
def explain_move(portfolio_id: str, period: Literal["day", "week", "month"]) -> MoveAttributionOut
# exposure/service.py
def get_exposure(portfolio_id: str) -> ExposureOut
def get_radar(portfolio_id: str) -> RadarOut
# planning/service.py (Persona 1, decisión 15)
def get_projection(portfolio_id: str) -> ProjectionOut
def get_agenda(portfolio_id: str) -> list[AgendaItemOut]
# status/service.py
def get_status(portfolio_id: str) -> StatusOut          # lee lo precalculado (< 200 ms)
def recompute(portfolio_id: str) -> StatusOut
```

### 4.3 Motor de impacto y exposición (Persona 2) → agentes y app

**`EventImpactOut`**: `GET /portfolios/{id}/events?days=7` devuelve una lista.

```json
{
  "event_id": "bce-2025-06",
  "portfolio_id": "laura",
  "title": "El BCE baja los tipos 0,25 puntos",
  "event_type": "central_bank",
  "occurred_at": "2026-11-08T18:02:00Z",
  "causal_chain": ["El BCE baja los tipos", "Baja la rentabilidad de los bonos", "Suben tus fondos de renta fija"],
  "impact_eur": "90.00", "low_eur": "40.00", "high_eur": "140.00",
  "impact_pct": "0.0021",
  "confidence": "media",
  "polarity": "neutral",
  "breakdown": [
    {"asset_id": "IE00BYX5MX67", "name": "Vanguard Global Bond", "value_eur": "10171.00",
     "impact_eur": "61.00", "market_eur": "61.00", "fx_eur": "0.00", "channel": "tipos"}
  ],
  "surprise": {"label": "en_linea", "expected": "-25", "actual": "-25", "metric": "rate_change_bp"},
  "explanation": "Poco. Tus fondos de renta fija suben ligeramente; en total, unos 90 euros a tu favor.",
  "explanation_status": "ok",
  "sources": [{"kind": "event", "...": "..."}],
  "calc_id": "calc_..."
}
```

Notas sobre los campos:

- `confidence`: `alta`, `media`, `baja`.
- `polarity`: `riesgo`, `oportunidad`, `neutral`.
- `explanation_status`: `pending`, `ok`, `template`.
- `surprise.label`: `mejor`, `peor`, `en_linea`. Es `null` si no hay consenso.
- El último eslabón de `causal_chain` lo pone el motor con plantilla: la clase de activo con mayor |impacto| de esa cartera ("Suben tus fondos de renta fija"). Así es personal y sin LLM.

Reglas que concretan `SPEC.md` §8.2:

- **`oportunidad`**: `low_eur > 0` **y** más del 50 % del impacto positivo cae en una clase de activo que está por debajo de su objetivo en el plan, es decir, el evento acerca la cartera al plan del usuario. `riesgo` si `high_eur < 0`. `neutral` en el resto.
- **`channel`**: es el `label` del canal del analizador con mayor contribución en ese activo. Los valores son "tipos", "bolsa", "tecnológicas", "petróleo", "dólar" y "resultados NVDA".
- **Resultados**: `company_moves` se aplica vía look-through (`w_{i,c} · m_c`). El activo **no** recibe además el shock de factor por esa misma empresa, para no contarlo dos veces. En eventos `earnings`, los factores seleccionados se aplican al resto del activo con su peso `(1 − w_{i,c})`.

**`ScenarioOut`**: `POST /portfolios/{id}/scenarios`, F25 (Si da tiempo). El backend se hace igual porque es el mismo cálculo.

```json
// request
{"factor_shocks": {"EQ_GLOBAL": "-0.10"}}
// response
{"factor_shocks": {"EQ_GLOBAL": "-0.10"}, "impact_eur": "-3120.00", "low_eur": "-3600.00", "high_eur": "-2640.00",
 "confidence": "alta", "breakdown": [{"...": "AssetImpact"}], "calc_id": "calc_..."}
```

**`ExposureOut`**: `GET /portfolios/{id}/exposure`.

```json
{
  "by_country":  [{"key": "US", "label": "Estados Unidos", "value_eur": "25850.00", "weight": "0.61"}],
  "by_sector":   [{"key": "information_technology", "label": "Tecnología", "value_eur": "...", "weight": "0.33"}],
  "by_currency": [{"key": "USD", "label": "Dólar", "value_eur": "...", "weight": "0.61"}],
  "top_companies": [{"key": "AAPL", "name": "Apple", "value_eur": "1610.00", "weight": "0.038",
                     "held_in": [{"asset_id": "IE00B4L5Y983", "weight_in_asset": "0.048"}, {"asset_id": "US0378331005", "weight_in_asset": "1"}]}],
  "overlap": [{"key": "AAPL", "name": "Apple", "weight": "0.038", "asset_ids": ["IE00B4L5Y983", "US0378331005"]}],
  "radiography": {
    "num_holdings": 3,
    "top_country": {"key": "US", "label": "Estados Unidos", "weight": "0.61"},
    "top_companies_group": {"n": 7, "weight": "0.19"}
  },
  "coverage_pct": "0.94",
  "as_of": "2026-06-30T00:00:00Z",
  "calc_id": "calc_..."
}
```

`radiography` alimenta el paso 2 del guion (F13 mínima). `num_holdings` cuenta fondos y ETF. `top_companies_group` son las 7 primeras empresas por peso; `N = 7` está fijo en configuración.

**`RadarOut`**: `GET /portfolios/{id}/radar`.

```json
{"items": [
  {"id": "rad_currency", "kind": "risk", "rule": "currency", "title": "El 61 % de tu dinero está en dólares",
   "detail": "Si el dólar cae frente al euro, tu cartera pierde aunque la bolsa no se mueva.",
   "value_eur": "25850.00", "weight": "0.61", "user_rule": null, "calc_id": "calc_..."},
  {"id": "rad_cheaper", "kind": "opportunity", "rule": "cheaper_contribution",
   "title": "Tu aportación de este mes compra más barato", "detail": "...",
   "value_eur": "210.00", "weight": "-0.034", "user_rule": {"source": "dca_plan", "ref": "dca_1"}, "calc_id": "calc_..."}
], "calc_id": "calc_..."}
```

Los valores de `rule` son `concentration`, `currency`, `drift`, `rebalance_with_dca`, `cheaper_contribution` y `tax_free_transfer`. **Invariante (test):** `kind == "opportunity"` ⇒ `user_rule != null`.

Los textos de `title` y `detail` salen de **plantillas deterministas**, sin LLM, con cifras del propio cálculo. No pasan por el guardián porque no son salida de agente. Aun así, un test aplica `forbidden.yaml` a todas las plantillas.

**`StatusOut`**: `GET /portfolios/{id}/status`. Se lee precalculado; objetivo < 200 ms.

```json
{"state": "atento", "state_label": "Atento",
 "total_eur": "42380.00", "change_week_pct": "-0.012",
 "sentence": "Tus fondos tecnológicos caen tras resultados. Toca para ver por qué.",
 "sentence_status": "ok",
 "reason": {"kind": "event", "event_id": "nvda-2025-02", "event_impact_eur": "-514.00"},
 "price_as_of": "2026-11-06T16:35:00Z",
 "computed_at": "2026-11-08T18:02:04Z", "calc_id": "calc_..."}
```

Valores y reglas:

- `state`: `tranquilo`, `atento`, `revisa_plan`.
- `sentence_status`: `ok`, `template`.
- `reason.kind`: `event`, `drift`, `none`.
- La regla para `atento` es la de `SPEC.md` §8.6.
- `revisa_plan` se activa si `|equity − target_equity| > drift_threshold`, con umbral por defecto **0,10** (decisión 7 de §8).

**`ProjectionOut`**: `GET /portfolios/{id}/projection`, F11 mínima para el paso 7.

```json
{"goal_amount_eur": "150000.00", "goal_year": 2040, "current_value_eur": "42380.00",
 "monthly_contribution_eur": "300.00",
 "scenarios": [
   {"name": "pesimista", "annual_return": "0.02", "value_at_goal_eur": "...", "reaches_goal": false},
   {"name": "base", "annual_return": "0.05", "value_at_goal_eur": "...", "reaches_goal": true},
   {"name": "optimista", "annual_return": "0.07", "value_at_goal_eur": "...", "reaches_goal": true}
 ],
 "on_track": true, "gap_eur": "0.00",
 "assumptions_source": {"kind": "assumption", "label": "Supuestos de rentabilidad por clase de activo", "ref": "data/seed/assumptions.json", "as_of": "...", "url": null},
 "calc_id": "calc_..."}
```

Cómo se calcula:

- Capitalización mensual y aportación mensual del DCA activo.
- `annual_return` de cada escenario es la media ponderada por la asignación **objetivo** de los rendimientos por clase de `data/seed/assumptions.json`. Ese fichero lo rellena Persona 5, con fuente citada y `"illustrative": true`.
- `on_track` equivale a que el escenario `base` alcanza la meta.

**`AgendaItemOut`**: `GET /portfolios/{id}/agenda`.

```json
[{"date": "2026-11-12T13:15:00Z", "kind": "central_bank", "title": "Reunión del BCE",
  "factor": "RATES_EUR", "exposed_weight": "0.24", "exposed_eur": "10171.00", "calc_id": "calc_..."},
 {"date": "2026-12-05T00:00:00Z", "kind": "dca", "title": "Tu aportación mensual", "factor": null,
  "exposed_weight": null, "exposed_eur": "300.00", "calc_id": "calc_..."}]
```

Cómo se calcula:

- La fuente es `data/events/agenda.json` (Persona 5), con fechas **relativas** al reloj de demo (`"offset_days": 4`), más los DCA activos.
- `exposed_eur` = Σ V_i de los activos con |β_{i,f}| ≥ 0,1 en el factor del evento. Para resultados de una empresa, es su exposición por look-through.

**`MoveAttributionOut`**: `GET /portfolios/{id}/move?period=week`, herramienta `explain_move`.

```json
{"period": "week", "start": "...", "end": "...",
 "change_eur": "-514.00", "change_pct": "-0.012",
 "by_asset": [{"asset_id": "...", "name": "...", "change_eur": "-420.00"}],
 "by_event": [{"event_id": "nvda-2025-02", "title": "...", "impact_eur": "-470.00", "low_eur": "...", "high_eur": "..."}],
 "unexplained_eur": "-44.00",
 "calc_id": "calc_..."}
```

`by_asset` sale de `portfolio.get_value_change`, con precios reales, sin flujos y con los ajustes de demo (decisión 17). `by_event` son los `event_impact` del periodo, que son **estimaciones**. `unexplained_eur = change_eur − Σ by_event` y se muestra como "otros movimientos del mercado".

### 4.4 Agentes (Persona 3) ↔ app y voz

**`AskRequest`**: `POST /portfolios/{id}/ask`, respuesta `text/event-stream`.

```json
{"question": "¿Por qué ha bajado?", "channel": "voice", "session_id": "ses_..."}
```

`channel` vale `voice` o `text`. `session_id` lo genera el frontend al abrir la app y sirve para saber si toca el aviso de IA.

Eventos SSE, uno por línea `data: {...}`, en este orden:

```json
{"type": "meta", "turn_id": "turn_...", "disclaimer": true}
{"type": "sentence", "turn_id": "turn_...", "index": 0, "text": "Sobre todo por tu fondo tecnológico: las grandes tecnológicas de EE. UU. han caído tras sus resultados.", "calc_ids": []}
{"type": "sentence", "turn_id": "turn_...", "index": 1, "text": "Te ha restado unos 470 euros.", "calc_ids": ["calc_..."]}
{"type": "done", "turn_id": "turn_...", "fallback_used": false, "blocked_count": 0, "first_sentence_ms": 812}
```

`{"type": "error", "turn_id": "...", "code": "UPSTREAM_UNAVAILABLE", "message": "..."}` sustituye a `done` si nada funcionó. Aun así, la plantilla de respaldo se intenta antes de devolver error.

Reglas del flujo:

- `disclaimer: true` → el frontend reproduce `GET /voice/disclaimer` (voz) o muestra el texto del aviso (texto) **antes** de la frase 0.
- Cada `sentence` ya pasó el guardián.
- `calc_ids` son las trazas de las cifras que contiene la frase. Las rellena el guardián al casar cada número.
- Si una frase se bloquea tras el reintento, el resto de la respuesta se sustituye por la plantilla (D-010) y `fallback_used` pasa a `true`.

**Contexto precargado del explicador** (`ExplainerContext`, D-011). Se construye por cartera, se cachea en el prompt y se invalida al cambiar el `calc_id` de `status`:

```json
{"portfolio_id": "laura", "as_of": "...", "persona_hint": "dinamico",
 "facts": [
   {"key": "total", "label": "patrimonio", "value": "42380.00", "unit": "EUR", "display": "42.380 euros", "calc_id": "calc_..."},
   {"key": "change_week", "label": "variación semanal", "value": "-514.00", "unit": "EUR", "display": "514 euros", "calc_id": "calc_..."},
   {"key": "evt.nvda-2025-02.impact", "label": "impacto de resultados de NVIDIA", "value": "-470.00", "unit": "EUR", "display": "470 euros", "calc_id": "calc_..."}
 ],
 "allocation": {"equity": "0.76", "fixed_income": "0.24"},
 "plan": {"on_track": true, "goal_year": 2040, "drift_exceeded": false},
 "events_7d": [{"event_id": "...", "title": "...", "causal_chain": ["..."], "polarity": "riesgo", "confidence": "media", "top_assets": ["..."]}],
 "status": {"state": "atento"}}
```

`facts[].display` es el formato que el prompt pide copiar literalmente. El explicador **solo** puede usar cifras que estén en `facts` o en resultados de herramientas.

**Herramientas del explicador** (`agents/tools.py`). Cada una devuelve el contrato del módulo dueño, más una lista `facts` con la misma forma que en el contexto:

| Herramienta | Llama a | Devuelve |
| --- | --- | --- |
| `get_portfolio()` | `portfolio.get_valued` | `PortfolioOut` + facts |
| `get_exposure()` | `exposure.get_exposure` | `ExposureOut` + facts |
| `get_events(days)` | `impact.list_event_impacts` | `list[EventImpactOut]` + facts |
| `estimate_impact(factor_shocks)` | `impact.estimate_scenario` | `ScenarioOut` + facts |
| `check_plan()` | `portfolio.get_plan` + `planning.get_projection` | `PlanOut` + `ProjectionOut` + facts |
| `explain_move(period)` | `impact.explain_move` | `MoveAttributionOut` + facts |

**Guardián** (`agents/guardian.py`, función pura y `mypy --strict`):

```json
// GuardianRequest
{"text": "Te ha restado unos 470 euros.", "channel": "voice", "question_kind": "impact", "sentence_index": 1,
 "evidence": [{"value": "-470.00", "unit": "EUR", "calc_id": "calc_..."}, {"value": "0.0025", "unit": "fraction", "calc_id": null, "source": "event:bce-2025-06"}]}
// GuardianVerdict
{"ok": true, "reasons": [], "figures": [{"text": "470 euros", "value": "470", "unit": "EUR", "matched_calc_id": "calc_..."}]}
// bloqueado
{"ok": false, "reasons": [{"code": "UNKNOWN_FIGURE", "detail": "«600 euros» no está en las herramientas"}], "figures": []}
```

Valores de los campos:

- `channel`: `voice`, `text`, `widget`, `alert`, `event_explanation`.
- `question_kind`: `impact`, `general` o `null`.
- `reasons[].code`: `FORBIDDEN_PATTERN`, `UNKNOWN_FIGURE`, `TOO_LONG`, `MISSING_EUR`.

Cómo funciona:

- **Evidencias:** los `facts` del contexto, los de las herramientas usadas en el turno y los números del evento (título, consenso).
- **Cifras:** se comparan **en valor absoluto** con las tolerancias de `SPEC.md` §9, porque el texto dice "te ha restado 470" para −470.
- **Formatos de número que entiende:** `1.295`, `1295`, `0,25`, `61 %`, `61%`, `-4,5 %`, y años de 4 dígitos que estén en las evidencias (`2040`).
- **Números en palabras** ("noventa"): el prompt los prohíbe y el guardián los trata como cifra desconocida si son mayores que diez.
- **Interfaz Python para otros módulos** (`agents/service.py`):
  - `write_event_explanation(impact: EventImpactOut) -> tuple[str, ExplanationStatus]`
  - `write_status_sentence(facts: StatusFacts) -> tuple[str, SentenceStatus]`
  - `write_alert_message(...) -> str`

**`AlertOut`**: `GET /portfolios/{id}/alerts`.

```json
[{"id": "alr_...", "event_id": "nvda-2025-02", "kind": "event_impact", "score": "0.82",
  "message": "Las tecnológicas de EE. UU. caen tras resultados: tu cartera, unos 470 euros menos.",
  "created_at": "...", "delivered": false, "calc_id": "calc_..."}]
```

`kind` vale `event_impact`, `dca_pending` o `drift`. El límite es de **2 avisos por semana ISO** por cartera, según `clock.now()`; los `dca_pending` no cuentan. `score = |impact_eur| / max(150, 0,005 · total)`, y se avisa si `score ≥ 1`.

### 4.5 Voz (Persona 5)

**`WS /api/v1/voice/stt`:**

```json
// cliente → servidor
{"type": "start", "sample_rate": 16000, "encoding": "pcm_s16le", "language": "es"}
// … frames binarios PCM …
{"type": "stop"}
// servidor → cliente
{"type": "partial", "text": "por qué ha"}
{"type": "final", "text": "¿Por qué ha bajado?"}
{"type": "error", "code": "UPSTREAM_UNAVAILABLE", "message": "..."}
```

**`POST /api/v1/voice/tts`:**

- Request: `{"turn_id": "turn_...", "index": 1}`.
- Respuesta: `audio/mpeg` en streaming.
- Si la frase no está aprobada en la caché del turno (TTL 5 min), devuelve 404 `SENTENCE_NOT_APPROVED`.
- La caché la escribe `agents` mediante `voice.service.register_approved(turn_id, index, text)`, una dependencia de Persona 3 hacia Persona 5 vía `service.py`.

**`GET /api/v1/voice/disclaimer`:** `audio/mpeg` pregenerado y guardado en `data/voice/disclaimer.mp3`. Dice: "Soy el asistente de KAIROS, una IA. No es asesoramiento financiero."

**Plan B:** si falla el STT, el frontend ofrece las 3 preguntas sugeridas, que llaman a `/ask` con `channel: "text"` y TTS igual. Si falla el TTS, la respuesta se muestra solo en texto.

### 4.6 Control de demo

Solo funciona con `DEMO_MODE=true`. Si no, devuelve 403 `DEMO_MODE_DISABLED`.

| Endpoint | Dueño | Efecto |
| --- | --- | --- |
| `POST /demo/reset` | Persona 1 | Recarga carteras y borra eventos, impactos y avisos. Llama a `events.reset()` y `impact.reset()` vía `service.py`. Con `{"preload": true}` (lo que usa el guion) reproduce además BCE y petróleo con `occurred_at = now() − 96 h` y `silent: true`: quedan fuera de las 72 h del estado Atento (paso 1 en Tranquilo, sin gastar avisos) y dentro de los 7 días del panel (paso 5) |
| `POST /demo/replay/{event_id}` | Persona 3 | Ejecuta el pipeline de §2. Body opcional `{"occurred_at": "<ISO>", "silent": false}`: con `occurred_at` el evento se fecha en ese instante en vez de `now()`; con `silent: true` no se generan avisos. Responde con `{"event_id", "portfolios": {"laura": "calc_...", "javier": "calc_..."}, "elapsed_ms"}` |
| `POST /demo/dca/run` | Persona 1 | Crea las ejecuciones pendientes de hoy |
| `PUT /demo/clock` | Persona 1 | `{"now": "2026-11-08T18:00:00Z"}` o `{"now": null}` para volver al reloj real |

---

## 5. Datos que el guion necesita (Persona 5, revisado con Persona 2)

Antes del lunes a las 14:00, los datos de semilla tienen que cumplir esto:

| Paso del guion | Condición sobre los datos |
| --- | --- |
| 1 | Laura: RV ≈ 76 %, objetivo 70 %, umbral 0,10, así que arranca en **Tranquilo**. Sin eventos en las últimas 72 h |
| 2 | Laura: 3 fondos/ETF, ≈ 61 % EE. UU. por look-through y ≈ 19 % en las 7 primeras empresas. Si los datos reales dan otra cifra, **se dice la cifra real** en el guion (el producto pone "ejemplo ilustrativo") |
| 3–4 | El evento que se usa en directo (resultados de tecnológicas) tiene `|impact_eur| ≥ max(150 €, 0,5 % del patrimonio)` para Laura. El ajuste de demo (decisión 17) hace que el patrimonio baje con el evento; basta con que la semana real previa no sea muy positiva (como mucho la mitad del impacto del evento), para que "¿por qué ha bajado?" cuadre |
| 6 | El mismo evento da impactos claramente distintos a Laura y a Javier |
| 7 | Laura tiene meta y DCA que dan `on_track: true` en el escenario base |

Las cifras de la tabla "La misma noticia, dos carteras" del producto son ilustrativas. El pitch usa las que calcule el motor.

---

## 6. Fases y tareas

Los días siguen el plan de 4 días del producto. Los IDs continúan los de `TABLERO.md`, y las tareas nuevas van al final de la lista de cada persona. Cada tarea está **hecha** cuando cumple su criterio, está en `main` y `make lint && make test` pasa.

### Fase 0 · Día 1, domingo 8 (hasta las 23:59): cimientos y contratos

Objetivo: que nadie dependa de nadie desde el lunes por la mañana.

| ID | Persona | Tarea | Hecho cuando | Depende de |
| --- | --- | --- | --- | --- |
| T-P1-01 | 1 | Esqueleto: Compose (db, backend, frontend, seed), Makefile, `config.py`, `core/{clock,db,errors,trace}.py`, CI | `make up` y `make test` en limpio | — |
| T-P1-03 | 1 | Esquemas comunes (§3) y de cartera (§4.1) + `examples/` + `portfolio/mock.py` + test que valida ejemplos | Ejemplos validan; mock sirve `/portfolios/laura` | T-P1-01 |
| T-P1-12 | 1 | `make gen-api` también copia `schemas/examples/*.json` a `frontend/src/api/mocks/` | Persona 4 importa los mocks | T-P1-03 |
| T-P2-01 | 2 | Esquemas §4.3 (impacto, exposición, radar, estado, proyección, agenda, move, escenario) + ejemplos + mocks | Ejemplos validan; los endpoints de P2 responden con mock | T-P1-01 |
| T-P3-01 | 3 | Esquemas §4.2 y §4.4 (`EventAnalysis`, `ShockSet`, Ask SSE, Guardián, `ExplainerContext`, `AlertOut`) + ejemplos + mocks; `/ask` mock emite SSE de ejemplo | Frontend recibe SSE mock | T-P1-01 |
| T-P5-10 | 5 | Contrato de voz §4.5 + mock (`/voice/tts` devuelve un mp3 fijo) | Frontend reproduce el mp3 mock | T-P1-01 |
| T-P4-01 | 4 | Vite + TS + Tailwind + TanStack Query; 3 pestañas (Inicio · Cartera · Pregunta) + ruta `/panel` sobre mocks | Navega sobre mocks | T-P1-12 |
| T-P5-01 | 5 | `assets.json` + `laura.json` / `javier.json` con plan y DCA según §5 | Cumple la fila 1 de §5 | — |
| T-P5-04 | 5 | Verificar IDs de Scribe v2 Realtime y Flash v2.5, y la voz en español; medir latencia | Anotado en `decisiones.md` | — |
| T-P3-02 | 3 + 5 | Confirmar los 3 eventos (decisión 5 de §8) y redactar `title`, `text`, `source_urls`, `consensus`, `fallback_chain` | JSON sin `observed` todavía | — |

### Fase 1 · Día 2, lunes 9: datos y motores

Al final del día tiene que funcionar lo de los días 1 y 2 del producto: alta por ISIN, look-through, eventos preparados, compra, venta, traspaso y DCA, impacto con rango, explicador con herramientas y guardián, todo contra el backend real. Lo del día 1 que no se haya terminado el domingo (look-through, eventos) tiene **como límite el lunes a las 14:00**.

| ID | Persona | Tarea | Hecho cuando | Depende de |
| --- | --- | --- | --- | --- |
| T-P1-02 | 1 | Modelos + migración (`SPEC.md` §6) | `alembic upgrade head` | T-P1-01 |
| T-P1-05 | 1 | `prices`: proveedor offline (CSV) + FX + `latest()` + `history()` | RF-03 | T-P5-03 (con CSV de prueba antes) |
| T-P1-04 | 1 | Alta de posiciones + seed + `/demo/reset` + `/assets/lookup` | RF-01, RF-02 | T-P1-02, T-P5-01 |
| T-P1-06 | 1 | Compra/venta FIFO con casos dorados | RF-04, RF-05 | T-P1-04 |
| T-P1-07 | 1 | Traspaso fondo → fondo + error con alternativa | RF-06 | T-P1-06 |
| T-P1-08 | 1 | DCA (planes, ejecución pendiente, confirmar/saltar, `/demo/dca/run`) | RF-07. Límite: martes 10:00 | T-P1-06 |
| T-P1-10 | 1 | `/plan` + `get_value_change` | RF-22 (datos) | T-P1-04 |
| T-P5-02 | 5 | Composición de los fondos/ETF de Laura y Javier (top-N + "Otros", `as_of`, fuente) | CSV completos; ≥ 90 % de cobertura en Laura | — |
| T-P5-03 | 5 | Históricos diarios de 2–3 años (activos y factores) + `observed` de los 3 eventos calculado de esos datos | `data/prices`, `data/factors`, replay completo | T-P3-02 |
| T-P2-02 | 2 | Casos dorados Laura/Javier (exposición, 3 eventos, proyección) en hoja | Revisado por otra persona | T-P5-01, T-P5-02 |
| T-P2-03 | 2 | Look-through, solapamientos y `radiography` | RF-08, RF-09 | T-P5-02 |
| T-P2-04 | 2 | `compute_betas.py` + `factor_beta` | Betas con R², error estándar y n | T-P5-03 |
| T-P2-05 | 2 | Motor de impacto: mercado, divisa, resultados, rango, confianza, polaridad; `estimate_scenario` comparte núcleo | RF-10 + dorados | T-P2-04 |
| T-P2-08 | 1 (decisión 15) | Proyección con DCA (`ProjectionOut`) | Dorado de Laura `on_track: true` | T-P1-10 (mock antes) |
| T-P3-03 | 3 | Analizador + `build_shockset` + pipeline de §2 + `/demo/replay` (impacto con mock de P2 al principio) | RF-11, RF-12; fallback probado | T-P3-02 |
| T-P3-04 | 3 | Guardián: patrones, cifras, forma; un test por patrón y por formato de número | RF-16 | T-P3-01 |
| T-P3-05 | 3 | Explicador: contexto precargado + herramientas + `/ask` SSE + reintento + plantilla | 3 preguntas tipo responden con FakeClaude y con Claude real | T-P3-04 |
| T-P4-02 | 4 | Pantalla de inicio simulada con widget (3 estados, color + palabra) | RF-13 visual | T-P4-01 |
| T-P4-03 | 4 | Alta de cartera + selector Laura/Javier (`?p=`) | RF-01, RF-02 | T-P4-01 |
| T-P4-04 | 4 | Operaciones (compra, venta, traspaso con error explicado) y DCA | RF-04–07 en UI | T-P4-01 |
| T-P5-05 | 5 | `voice/` backend: STT por WS, TTS de frases aprobadas, disclaimer | Audio de ida y vuelta con frase fija | T-P5-04 |

### Fase 2 · Día 3, martes 10 (hasta las 18:00): experiencia e integración

**Hito 18:00:** los 8 pasos del guion seguidos en `main`, en modo offline salvo Claude y ElevenLabs. A las 18:00 Persona 1 decide qué "Si da tiempo" entra.

| ID | Persona | Tarea | Hecho cuando | Depende de |
| --- | --- | --- | --- | --- |
| T-P1-09 | 1 | `/traces/{calc_id}` con `parent_calc_ids` | RF-19 | T-P1-02 |
| T-P1-14 | 1 | Ajuste de demo: `portfolio.service.apply_demo_adjustment(portfolio_id, event_id, breakdown, calc_id)` (lo llama `events` tras el impacto) + `demo_adjustments` en la valoración + borrado en `/demo/reset` | Tras el replay, `/portfolios/laura` y `/status` reflejan el impacto con etiqueta y traza | T-P1-04, T-P2-05 |
| T-P1-11 | 1 | Integración: quitar mocks del backend módulo a módulo; `/demo/clock`; smoke del guion por API (`scripts/demo_smoke.py`) | Smoke en verde | Todas las de Fase 1 |
| T-P2-06 | 2 | `status` precalculado + `recompute` + frase vía `agents.write_status_sentence` | RF-13; `/status` < 200 ms | T-P2-05, T-P3-05 |
| T-P2-07 | 2 | Radar (6 reglas, plantillas, invariante de oportunidad) | RF-18 | T-P2-03, T-P1-08 |
| T-P2-10 | 1 (decisión 15) | Agenda (`agenda.json` + DCA + exposición por factor) | Bloque del panel con datos | T-P2-04, T-P5-11 |
| T-P2-11 | 2 | `explain_move` | "¿Por qué ha bajado?" con dato real | T-P1-10, T-P2-05 |
| T-P3-06 | 3 | Avisos: score, umbral, límite semanal, mensaje validado | RF-23 (`kind=event_impact` es MVP porque lo usa el paso 3) | T-P2-05 |
| T-P3-08 | 3 | Explicaciones de evento por cartera + invalidación del contexto precargado | `explanation_status: ok` en los 3 eventos × 2 carteras | T-P3-03, T-P2-05 |
| T-P4-05 | 4 | Panel: resumen, eventos (cadena, €, rango, confianza, filtro), exposición, radar, agenda | RF-17 | T-P2-* (mocks antes) |
| T-P4-06 | 4 | "¿De dónde sale?" → traza desde cualquier cifra | RF-19 | T-P1-09 |
| T-P4-07 | 4 | Avisos de IA y "no es asesoramiento"; accesibilidad | RF-20, RNF-11 | — |
| T-P4-09 | 4 | Polling de `/status` y `/alerts` cada 5 s; aviso en pantalla de inicio (paso 3) | El widget cambia solo tras un replay | T-P2-06, T-P3-06 |
| T-P5-06 | 5 | `src/voice/`: push-to-talk, cola de audio por frase, disclaimer, plan B de preguntas sugeridas | RF-14 de punta a punta | T-P5-05, T-P3-05 |
| T-P5-11 | 5 | `assumptions.json`, `agenda.json`, `DEMO_CLOCK` y revisión de los datos contra §5 | Las 5 filas de §5 se cumplen | T-P2-03, T-P2-05 |
| T-P5-12 | 5 | Medir latencia de voz (10 intentos) | 8/10 por debajo de 2 s o, si no, cambiar de modelo (decisión 4) | T-P5-06 |

### Fase 3 · Martes 18:00 → miércoles 21:00: endurecer y entregar

**Congelación el miércoles a las 16:00** (solo arreglos). **Entrega antes de las 21:00.**

| ID | Persona | Tarea | Hecho cuando |
| --- | --- | --- | --- |
| T-P3-07 | 3 | Evaluación de 30 preguntas (10 por tipo + 10 trampa "¿vendo?") | 0 órdenes de compraventa; tasa de bloqueo anotada |
| T-P4-08 | 4 | Playwright del guion de demo | E2E en verde en offline con fakes |
| T-P2-09 | 2 + 4 | Escenarios ¿Y si…? en el panel (si a las 18:00 estaba en verde) | RF-21, < 500 ms |
| T-P2-12 | 2 | Calibrar umbrales con datos reales (estado, avisos, confianza) | Guion estable 3 veces seguidas |
| T-P1-13 | 1 | Prueba en máquina limpia con el ZIP | `docker compose up` + README sin ayuda |
| T-P5-07 | 5 | README | Otra persona lo ejecuta sin ayuda |
| T-P5-08 | 5 | PDF de una cara + PPT + diapositiva de arquitectura | Revisado por el equipo |
| T-P5-09 | 5 | Vídeo de respaldo + ZIP + formulario BEST UC3M | Enviado antes de las 21:00 |
| — | Todas | 3 ensayos cronometrados | < 3 min |

**Regla de recorte** (del producto): si el martes a las 15:00 el guion no va, se recorta en este orden:

1. Agenda.
2. Radar, dejando solo `currency` y `cheaper_contribution`.
3. Operaciones en la UI, dejando solo comprar.

**No se recortan nunca** voz, widget ni motor de impacto.

---

## 7. Pruebas

Se mantiene `INGENIERIA.md` §9 y se añaden cinco pruebas:

- Validación de todos los `schemas/examples/*.json` en CI (T-P1-03).
- Test del invariante "oportunidad ⇒ `user_rule`" (T-P2-07).
- Test "las plantillas de radar, estado y avisos no contienen patrones prohibidos" (T-P3-04).
- Test "`EventAnalysis` sin dígitos" y test de fallback del analizador (T-P3-03).
- Test "`/voice/tts` rechaza frases no aprobadas" (T-P5-05).

---

## 8. Preguntas abiertas: decisiones

Se cierran las preguntas abiertas de `kairos-spec.md` y las técnicas de `TABLERO.md` §7.

| # | Pregunta | Decisión | Origen |
| --- | --- | --- | --- |
| 1 | Nombre definitivo | KAIROS | Ya decidido en el producto |
| 2 | Criterios y duración del hackathon | Rúbrica del producto; Dom 8 tarde → Mié 11 23:59, entrega interna antes de las 21:00 | Producto + `TABLERO.md` Q2 |
| 3 | ¿Widget nativo o web? | Simulado en web móvil; D-004 pasa a **Aceptada** | El alcance del producto lo dice |
| 4 | Proveedor de LLM y voz | Claude (Haiku 5.5 rápido y Sonnet 5.5 profundo, por `.env`) + ElevenLabs (Scribe v2 Realtime, Flash v2.5); D-012 pasa a **Aceptada**. Si la latencia de T-P5-12 falla, se cambia de modelo o de voz, no de proveedor | Mi decisión |
| 5 | Qué 3 eventos usar en el replay | (a) **BCE 5 jun 2025**, bajada de 25 pb (con consenso); (b) **petróleo 13 jun 2025**, ataque de Israel a Irán y salto del Brent; (c) **resultados que hunden a las tecnológicas de EE. UU.**: propuesta NVIDIA, resultados del 26 feb 2025 y caída del 27 feb. Persona 5 confirma fechas y movimientos con los datos en T-P5-03; si un evento no muestra movimiento claro, se cambia por otro del mismo tipo. Opcional (S): un día de dólar débil | Mi propuesta, a verificar |
| 6 | Fuente de consenso para la sorpresa | Solo para el BCE (consenso de mercado citado en prensa, guardado en el JSON). En los demás eventos `consensus: null` y `surprise: null` | Mi decisión |
| 7 | Laura arranca en "Revisa tu plan" pero el paso 1 la quiere en Tranquilo | `drift_threshold` por defecto **10 pp**. 76 % frente a 70 % da Tranquilo; el ejemplo del producto (82 % frente a 70 %) sigue dando "Revisa tu plan". No se cambia ni el producto ni la cartera | Mi decisión |
| 8 | "¿Voy bien?" (paso 7) depende de F11 ("Si da tiempo"); la radiografía (paso 2) es F13 ("Si da tiempo") | Pasan a MVP **en versión mínima**: plan + proyección (`ProjectionOut`) y el bloque `radiography` de `ExposureOut`. El resto de F11 y F13 sigue en "Si da tiempo" | Mi decisión: el guion es producto |
| 9 | Modelo de negocio del pitch | B2B2C como vía principal (marca blanca para brókers y neobancos), B2C freemium para validar | Ya en el producto |
| 10 | Hito del guion completo | **Martes 10 a las 18:00** (producto), no a las 23:00 (`TABLERO.md`) | Producto |
| 11 | Magnitud de los shocks: ¿LLM o datos? | Datos (`observed`); el LLM elige canales y redacta | Mi decisión (regla 1 de `CLAUDE.md`) |
| 12 | Precios "moviéndose en directo" en el paso 1 | Si hay `MARKET_DATA_API_KEY`, el proveedor real refresca acciones y ETF cada 60 s; sin clave (jurado), offline con "precio a fecha X" | Mi decisión |
| 13 | ¿El ZIP funciona sin claves de Claude y ElevenLabs? | Las claves son **necesarias** para la IA (el producto pide en el README las claves de Claude y ElevenLabs en `.env.example`). Sin claves, la app arranca: el explicador responde con plantillas construidas con datos del motor (las mismas del guardián, `fallback_used: true`) y no hay audio. No hay respuestas pregrabadas | Mi decisión |
| 14 | ¿El paso 1 da de alta la cartera en directo? | El guion carga la **cartera de ejemplo** ("o cartera de ejemplo", lo permite el producto). El alta por ISIN (F1) se construye igual, pero no está en la ruta crítica del martes a las 18:00 | Mi decisión |
| 15 | Carga de Persona 2 (camino crítico) | La **proyección** (T-P2-08) y la **agenda** (T-P2-10) pasan a **Persona 1** en una carpeta nueva `backend/app/planning/` que es suya; llaman a `impact`/`exposure` solo vía `service.py`. Los endpoints `/projection` y `/agenda` pasan a Persona 1 | Mi decisión |
| 17 | ¿El replay cambia el patrimonio mostrado? | **Sí, solo en modo demo**: la valoración suma el impacto central estimado de cada posición, con la etiqueta "Estimación tras el evento" y su `calc_id`. Sustituye a D-009 en lo de "sin reescribir precios" (los precios no se tocan; se añade un ajuste aparte) | **Equipo (decidido por el humano)** |
| 16 | Año de `DEMO_CLOCK` | 2026 (fechas actuales). `data/prices` llega hasta la fecha de descarga; los eventos son de 2025 y solo aportan `observed` | Mi decisión |
| — | Reparto de nombres en Persona 1–5 y disponibilidad (`TABLERO.md` Q1, Q8) | **Las decide el equipo**; no afectan al diseño | Equipo |

---

## 9. Qué cambia en los documentos vivos tras aprobar este diseño

Lo hace la sesión que ejecute el plan, en un PR `docs:` propio y antes de cualquier código:

- `SPEC.md`:
  - §5: contratos completos o enlace a este documento.
  - §8.2: polaridad, resultados sin doble conteo, unidad de `RATES_EUR`.
  - §8.6: umbral 10 pp.
  - §10: voz en tres tramos.
  - §11: endpoints `agenda`, `move` y `voice/disclaimer`.
  - §12: formato de `observed` y `consensus`.
  - §13: `drift_threshold`.
- `decisiones.md`:
  - D-004 y D-012 → Aceptada. D-009 → Sustituida por la nueva decisión del ajuste de demo (decisión 17).
  - Nuevas decisiones desde D-016 con las decisiones 4–8 y 10–17 de §8, y "ejemplos JSON como fuente de los mocks".
- `TABLERO.md`:
  - "Persona 1–5" como nombres de rol.
  - Tareas nuevas (T-P1-11 a 14, T-P2-10 a 12, T-P3-08, T-P4-09, T-P5-10 a 12).
  - Hito del martes a las 18:00.
  - Q3, Q4, Q5 y Q6 cerradas.
- `INGENIERIA.md`:
  - RF-22 (mínimo) y la radiografía pasan a M.
  - Nota de §4 resuelta.
- `CLAUDE.md`: enlace a este documento en el mapa.

## 10. Lo que queda a criterio de quien construye

- Nombres internos de funciones privadas, estructura de componentes React y estilos (dentro de las reglas de `CLAUDE.md`).
- Redacción de las plantillas (sin cifras inventadas y sin patrones prohibidos).
- Prompts del analizador y del explicador (sin cifras de ejemplo; marcador `<IMPORTE>`).
- Qué fondos y ETF concretos forman las carteras, siempre que cumplan §5.
- Formato de audio exacto entre backend y ElevenLabs, siempre que el navegador reciba `audio/mpeg`.
