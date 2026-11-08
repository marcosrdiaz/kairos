"""`scripts/compute_betas.py` de punta a punta, en un proceso aparte como lo lanza `make betas`.

En otro proceso porque el fixture `db` ya importa `app.models`; el script debe registrar las
tablas por su cuenta (sin eso, la FK `factor_beta.asset_id → asset.id` no se resuelve).
"""

import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from app.core.db import session_scope
from app.impact import repository
from app.portfolio.models import Asset
from app.schemas.common import Factor

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "compute_betas.py"


def _seed_assets() -> list[str]:
    raw = json.loads((ROOT / "data" / "seed" / "assets.json").read_text(encoding="utf-8"))
    cols = {c.name for c in Asset.__table__.columns}
    with session_scope() as session:
        for a in raw["assets"]:
            row = {k: v for k, v in a.items() if k in cols}
            if row.get("ter") is not None:
                row["ter"] = Decimal(str(row["ter"]))
            session.add(Asset(**row))
    return [a["id"] for a in raw["assets"] if a["price_source"].startswith("yahoo:")]


def _run() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT / "backend",
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )


def test_script_writes_all_betas_and_can_be_repeated(db: None) -> None:
    yahoo_ids = _seed_assets()

    first = _run()
    second = _run()

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    betas = repository.get_betas(yahoo_ids)
    assert len(betas) == len(yahoo_ids) * len(Factor)
    assert {e.asset_id for e in betas} == set(yahoo_ids)
