### D-008 · `Decimal` para dinero y participaciones
- Fecha: 2026-11-08 · Autor: equipo · Estado: Propuesta
- Decisión: `Decimal` en Python, `NUMERIC` en BD, `string` en JSON (Pydantic serializa `Decimal` como texto); el frontend formatea con `Intl.NumberFormat('es-ES')`.
- Motivo: evitar errores de redondeo visibles en la demo (p. ej. 0,30000000004 €).
- Consecuencias: pandas solo dentro de `impact/` y se convierte a `Decimal` en la salida.
