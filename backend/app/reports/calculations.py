"""Pure, DB-free financial calculations (RB-006, section 7.1 of the spec).

Kept free of SQLAlchemy/session dependencies so the critical formulas can be
unit-tested directly and reused by dashboard, closing and forecast services
without duplicating rounding/edge-case logic.
"""

import statistics
from decimal import Decimal

from app.core.money import quantize_money

NOT_APPLICABLE = None


def realized_savings(realized_income: Decimal, realized_expenses: Decimal) -> Decimal:
    """Economia realizada = receitas realizadas - despesas realizadas (RB-006).

    Transfers must already be excluded from both inputs by the caller (RB-004).
    """
    return quantize_money(realized_income - realized_expenses)


def savings_rate(savings: Decimal, income: Decimal) -> Decimal | None:
    """Taxa de poupança = economia / receita * 100. None (N/A) quando receita é zero."""
    if income == 0:
        return NOT_APPLICABLE
    return (savings / income * Decimal("100")).quantize(Decimal("0.01"))


def absolute_variance(actual: Decimal, planned: Decimal) -> Decimal:
    """Desvio absoluto = realizado - planejado."""
    return quantize_money(actual - planned)


def percentage_variance(actual: Decimal, planned: Decimal) -> Decimal | None:
    """Desvio percentual = (realizado - planejado) / planejado * 100. None quando planejado é zero."""
    if planned == 0:
        return NOT_APPLICABLE
    return ((actual - planned) / planned * Decimal("100")).quantize(Decimal("0.01"))


def savings_capacity_estimate(monthly_history: list[Decimal]) -> dict[str, Decimal | str | None]:
    """Section 7.2: no fixed contribution required from the user — capacity is
    observed from realized history. Default recommendation is the median of
    the last 6 complete months (a robust estimate resistant to one
    extraordinary month), with averages kept alongside for transparency.
    """
    if not monthly_history:
        return {
            "average_3m": None,
            "average_6m": None,
            "average_12m": None,
            "median_6m": None,
            "trend": "INSUFFICIENT_DATA",
            "recommended": Decimal("0.00"),
        }

    def avg(values: list[Decimal]) -> Decimal | None:
        return quantize_money(sum(values) / len(values)) if values else None

    last_3 = monthly_history[-3:]
    last_6 = monthly_history[-6:]
    last_12 = monthly_history[-12:]

    median_6 = quantize_money(Decimal(str(statistics.median(last_6)))) if last_6 else None
    recommended = median_6 if median_6 is not None else (avg(monthly_history) or Decimal("0.00"))

    if len(last_6) >= 2:
        trend = "UP" if last_6[-1] > last_6[0] else "DOWN" if last_6[-1] < last_6[0] else "STABLE"
    else:
        trend = "INSUFFICIENT_DATA"

    return {
        "average_3m": avg(last_3),
        "average_6m": avg(last_6),
        "average_12m": avg(last_12),
        "median_6m": median_6,
        "trend": trend,
        "recommended": recommended,
    }


def residual_budget(period_budget: Decimal, already_planned: Decimal) -> Decimal:
    """Orçamento residual = orçamento do período - valores já planejados na categoria (7.4).

    Prevents double-counting a variable expense in forecasts that already
    has specific planned transactions in the same category.
    """
    residual = period_budget - already_planned
    return quantize_money(residual) if residual > 0 else Decimal("0.00")
