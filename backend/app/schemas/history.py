"""Evolución del valor de una cartera (T2-18): `GET /portfolios/{id}/history?period=`.

La serie usa precios de cierre reales (`prices.history`) y las participaciones que había en cada
fecha según el libro de operaciones. No incluye los ajustes de demo del replay (D-031).
"""

from enum import StrEnum

from app.schemas.common import ContractModel, Fraction, Money, SourceRef, UtcDatetime
from app.schemas.portfolio import CalcId


class HistoryPeriod(StrEnum):
    ONE_WEEK = "1w"
    ONE_MONTH = "1m"
    SIX_MONTHS = "6m"
    ONE_YEAR = "1y"
    MAX = "max"


class PortfolioHistoryPoint(ContractModel):
    """Un cierre de la serie.

    - `change_eur` / `change_pct`: variación respecto al punto anterior (`null` en el primero).
      Incluye las aportaciones o retiradas de entre medias: `flows_eur` dice cuánto fue dinero
      que entró o salió, para no confundirlo con una subida o una bajada.
    - `change_pct` es una fracción a 4 decimales (0.0123 = 1,23 %) sobre el valor anterior.
    """

    date: UtcDatetime
    """Día del cierre (00:00 UTC)."""
    value_eur: Money
    change_eur: Money | None = None
    change_pct: Fraction | None = None
    flows_eur: Money


class PortfolioHistoryOut(ContractModel):
    """Serie de valor de la cartera en el periodo pedido.

    - `points`: en orden de fecha. Un punto por día hábil hasta un año; con `max`, uno por semana
      (y siempre el último día). Se omiten las fechas sin precio de algún activo: nunca se rellenan.
    - `start_value_eur` / `end_value_eur`: valor del primer y del último punto.
    - `net_flows_eur`: dinero aportado (+) o retirado (−) entre el primer y el último punto
      (compras, DCA, ventas), para no confundir aportaciones con rentabilidad.
    - `calc_id`: traza `valuation` con la serie, las participaciones y las fuentes.
    """

    portfolio_id: str
    period: HistoryPeriod
    points: list[PortfolioHistoryPoint]
    start_value_eur: Money
    end_value_eur: Money
    net_flows_eur: Money
    calc_id: CalcId
    sources: list[SourceRef]
