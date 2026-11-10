### D-101 · Catálogo fijo ampliado y comprobado en Yahoo en lugar de catálogo abierto en el MVP (T4-26)
- Fecha: 2026-11-10 · Autor: Alons · Estado: Propuesta
- Contexto: T4-07 (catálogo abierto: buscar en Yahoo cualquier activo y darlo de alta) llegó a estar hecha en dos PR (#123 y #124). Al probarla, se vio que mete en la app activos que nadie ha comprobado: sin composición, con la cobertura de la exposición más baja, con la clase de activo deducida del nombre y con cotizaciones en divisas que no sabemos convertir. Para un MVP es mejor un catálogo cerrado y comprobado.
- Decisión:
  - **T4-07 se aparca** hasta después de la entrega. Sus ramas se conservan sin merge.
  - **`data/seed/assets.json` pasa de 17 a 25 activos.** Solo entra un activo si cumple tres cosas:
    1. Yahoo lo da en EUR o USD, con al menos 2 años de cierres y cotización reciente. Lo comprueba `scripts/check_catalog.py`, con un test `live`.
    2. Tiene sus cierres en `data/prices` hasta el 6 nov (el día de la demo). Se descargan con `fetch_prices.py --assets … --until 2026-11-06`, que no toca el resto de CSV ni los factores, así que las cifras de Laura y Javier no cambian.
    3. Su composición es verificable.
  - **Los 8 nuevos:**
    - **ETF:** Vanguard S&P 500 (VUSA), SPDR MSCI World (SPPW) y Vanguard FTSE All-World Dist (VWRL). TER contrastado en justETF el 10-11-2026.
    - **Acciones:** Amazon, Alphabet, Meta, Tesla y ASML.
  - **Composición de los ETF nuevos:** replican el mismo índice que un ETF que ya estaba (CSPX, IWDA y VWCE). Su CSV es el de ese ETF, y la fuente lo dice («Mismo índice (S&P 500) que IE00B5BMR087: …»).
  - **Acciones:** solo las que aparecen con su ticker en la composición del MSCI World (IWDA). Así su país y su sector salen de ahí y los solapes con los fondos se detectan (D-052; `test_direct_stocks_share_keys_with_fund_companies`).
- Motivo: todo activo del catálogo se valora en demo y en directo, tiene betas y look-through, sin ningún dato inventado.
- Alternativas descartadas:
  - **Catálogo abierto (T4-07):** ver el contexto.
  - **Añadir más activos sin composición** (Santander, BBVA, Telefónica, Repsol, LVMH, ETF de Europa, emergentes, bonos o monetarios): la exposición tendría huecos y los tests de composición fallarían. Inventar sus composiciones rompería la regla de no inventar datos.
- Impacto:
  - Para ampliar el catálogo con esos activos, falta la composición oficial de cada uno (ficheros de la gestora, como los de T1-08) o T4-08 (composiciones automáticas).
  - El distintivo del ticker (T2-28) muestra la pastilla neutra para los emisores nuevos (SPDR, Amazon, Alphabet, Meta, Tesla, ASML) hasta que se les asigne color.
  - La interfaz no cambia: el buscador del alta ya lee `GET /assets/lookup`.
