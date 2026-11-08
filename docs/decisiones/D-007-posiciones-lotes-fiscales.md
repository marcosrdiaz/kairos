### D-007 · Posiciones derivadas de lotes fiscales
- Fecha: 2026-11-08 · Autor: P1 (propuesta inicial) · Estado: Propuesta
- Contexto: hay que soportar FIFO en ventas y traspasos que conservan coste y antigüedad.
- Decisión: tablas `transaction` (libro, fuente de verdad) y `tax_lot`; la posición se calcula sumando lotes. No hay tabla `position`.
- Motivo: FIFO y traspasos salen naturales; una tabla de posiciones con precio medio pierde la fecha de cada compra.
- Consecuencias: el alta inicial crea un lote por activo con la fecha indicada.
