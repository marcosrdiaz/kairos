"""Evaluación de respuestas (T3-01). La lógica vive en `scripts/eval_answers.py`."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "eval_answers.py"


def load_script() -> ModuleType:
    """Importa `scripts/eval_answers.py` (no está en un paquete) una sola vez."""
    if "eval_answers" in sys.modules:
        return sys.modules["eval_answers"]
    spec = importlib.util.spec_from_file_location("eval_answers", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["eval_answers"] = module  # las dataclasses lo buscan al crearse
    spec.loader.exec_module(module)
    return module
