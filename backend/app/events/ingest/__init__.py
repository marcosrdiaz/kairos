"""Ingesta de noticias reales (T4-05): las fuentes crean eventos (`EventIn` con `text` y
`source_urls`) sin pasar por el replay, y los procesa el pipeline de siempre vía
`events.service.ingest`.

Fuentes: notas de política monetaria del BCE (`ecb.py`). Una pasada: `runner.run_once()` o
`python -m app.events.ingest`.
"""
