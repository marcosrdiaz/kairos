from fastapi import APIRouter

from app.config import get_settings
from app.core import clock

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str | bool]:
    """Comprobación de Docker. No toca la base de datos."""
    return {
        "status": "ok",
        "demo_mode": get_settings().demo_mode,
        "now": clock.now().isoformat().replace("+00:00", "Z"),
    }
