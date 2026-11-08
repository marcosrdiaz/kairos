### D-002 · El LLM nunca calcula cifras
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: una cifra inventada destruye la confianza y la rúbrica premia madurez técnica.
- Decisión: todas las cifras salen de `portfolio` o `impact`; Claude solo redacta a partir de resultados de herramientas; el guardián comprueba que cada número del texto existe en esos resultados.
- Motivo: trazabilidad (principio 6) y argumento para el jurado.
- Consecuencias: herramientas del explicador devuelven valores ya redondeados para mostrar; prompts sin cifras de ejemplo.
