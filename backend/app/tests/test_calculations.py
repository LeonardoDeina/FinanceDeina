from decimal import Decimal

from app.reports.calculations import (
    absolute_variance,
    percentage_variance,
    realized_savings,
    residual_budget,
    savings_capacity_estimate,
    savings_rate,
)


def test_realized_savings_excludes_nothing_itself_just_subtracts():
    assert realized_savings(Decimal("3500.00"), Decimal("2730.00")) == Decimal("770.00")


def test_savings_rate_is_percentage():
    assert savings_rate(Decimal("770.00"), Decimal("3500.00")) == Decimal("22.00")


def test_savings_rate_not_applicable_when_no_income():
    assert savings_rate(Decimal("-50.00"), Decimal("0.00")) is None


def test_absolute_variance_matches_spec_example():
    assert absolute_variance(Decimal("2730.00"), Decimal("2550.00")) == Decimal("180.00")


def test_percentage_variance_not_applicable_when_planned_is_zero():
    assert percentage_variance(Decimal("50.00"), Decimal("0.00")) is None


def test_percentage_variance_regular_case():
    assert percentage_variance(Decimal("110.00"), Decimal("100.00")) == Decimal("10.00")


def test_residual_budget_prevents_double_counting():
    # 400 budgeted for groceries, 250 already covered by specific planned transactions
    assert residual_budget(Decimal("400.00"), Decimal("250.00")) == Decimal("150.00")


def test_residual_budget_never_negative():
    assert residual_budget(Decimal("400.00"), Decimal("500.00")) == Decimal("0.00")


def test_savings_capacity_uses_median_of_last_six_months_and_resists_outlier():
    # one extraordinary month (2000) should not dominate the recommendation
    history = [Decimal(v) for v in [300, 320, 310, 2000, 290, 305]]
    estimate = savings_capacity_estimate(history)
    assert estimate["median_6m"] == Decimal("307.50")
    assert estimate["recommended"] == Decimal("307.50")
    assert estimate["average_6m"] > estimate["median_6m"]  # mean is pulled up by the outlier


def test_savings_capacity_with_no_history():
    estimate = savings_capacity_estimate([])
    assert estimate["trend"] == "INSUFFICIENT_DATA"
    assert estimate["recommended"] == Decimal("0.00")
