"""Cifras reales para el PDF y la presentación (T6-02): las calcula el backend, no se escriben a mano.

Uso (desde backend/, con DATABASE_URL apuntando a un SQLite temporal ya migrado y con seed y betas):
    python -I -X utf8 <este fichero>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from app.events import service as events_service  # noqa: E402
from app.exposure import service as exposure_service  # noqa: E402
from app.impact import service as impact_service  # noqa: E402
from app.portfolio import service as portfolio_service  # noqa: E402

for pid in ("laura", "javier"):
    p = portfolio_service.get_valued(pid)
    print(f"[{pid}] total_eur={p.total_eur} allocation={p.allocation}")
    exp = exposure_service.get_exposure(pid)
    print(f"[{pid}] exposure:", exp.model_dump_json()[:1500])

for event_id in ("bce-2025-06", "oil-2025-06", "nvda-2025-02"):
    events_service.replay(event_id)

for pid in ("laura", "javier"):
    for impact in impact_service.list_event_impacts(pid, 30):
        print(
            f"[{pid}] {impact.event_id}: impact={impact.impact_eur} "
            f"range=[{impact.low_eur}, {impact.high_eur}] pct={impact.impact_pct} "
            f"conf={impact.confidence.value} calc_id={impact.calc_id}"
        )
