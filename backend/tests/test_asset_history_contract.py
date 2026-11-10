"""Contrato de T2-23 que no depende de la base de datos.

La ruta `GET /portfolios/{id}/positions/{asset_id}/history` se prueba con datos reales en
`test_asset_history.py`.
"""

from app.schemas.impact import AssetImpact

NVDA = "US67066G1040"


def test_asset_impact_range_is_optional() -> None:
    """Los impactos guardados antes de T2-23 no traen el rango por posición."""
    old = AssetImpact.model_validate(
        {
            "asset_id": NVDA,
            "name": "NVIDIA Corp.",
            "value_eur": "1258.67",
            "impact_eur": "-180.00",
            "market_eur": "-180.00",
            "fx_eur": "0.00",
            "channel": "resultados NVDA",
        }
    )

    assert old.low_eur is None and old.high_eur is None
