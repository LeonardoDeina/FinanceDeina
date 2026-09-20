import json
from decimal import Decimal

from app.currency.schemas import ConversionQuoteResponse
from app.forecasting.schemas import ForecastRunRead


def test_money_values_serialize_as_strings_not_floats():
    """RB-001 / spec 14: monetary values must never round-trip through
    float, so the API contract keeps Decimal precision by serializing as
    JSON strings rather than JSON numbers."""
    quote = ConversionQuoteResponse(
        from_code="EUR", to_code="USD", on_date="2026-01-01", rate=Decimal("1.10"),
        amount=Decimal("1000.00"), converted_amount=Decimal("1100.00"),
    )
    payload = json.loads(quote.model_dump_json())
    assert payload["converted_amount"] == "1100.00"
    assert isinstance(payload["converted_amount"], str)


def test_forecast_amounts_preserve_decimal_precision_end_to_end():
    data = {
        "id": 1,
        "run_at": "2026-01-01T00:00:00",
        "horizon_end": "2026-03-01",
        "scenario_name": None,
        "currency": "EUR",
        "starting_balance": Decimal("1000.10"),
        "projected_ending_balance": Decimal("7000.30"),
        "monthly_items": [],
    }
    forecast = ForecastRunRead.model_validate(data)
    assert forecast.starting_balance == Decimal("1000.10")
    assert json.loads(forecast.model_dump_json())["starting_balance"] == "1000.10"
