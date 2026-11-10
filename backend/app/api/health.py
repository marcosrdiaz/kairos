from fastapi import APIRouter

from app.config import get_settings
from app.core import clock

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str | bool]:
    """Comprobación de Docker, con el modo (`demo` o `production`) y el proveedor de precios
    (D-065). No toca la base de datos."""
    settings = get_settings()
    return {
        "status": "ok",
        "mode": settings.mode,
        "demo_mode": settings.demo_mode,
        "market_data_provider": settings.market_data_provider,
        "now": clock.now().isoformat().replace("+00:00", "Z"),
    }
