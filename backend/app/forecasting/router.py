import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.forecasting.models import ForecastMonthlyItem, ForecastRun
from app.forecasting.schemas import ForecastRunRead, ForecastRunRequest, SavingsCapacityRead
from app.forecasting.service import run_forecast
from app.reports.aggregation import actual_totals, convert_period_totals, month_bounds
from app.reports.calculations import realized_savings, savings_capacity_estimate
from app.users.service import get_or_create_profile

router = APIRouter(prefix="/forecasts", tags=["forecasting"])


@router.post("/run", response_model=ForecastRunRead, status_code=201)
def create_forecast_run(payload: ForecastRunRequest, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    today = dt.date.today()
    horizon_end = payload.horizon_end or (today + dt.timedelta(days=payload.horizon_days))

    result = run_forecast(db, profile, horizon_end, account_ids=payload.account_ids)

    forecast_run = ForecastRun(
        user_id=profile.id,
        horizon_end=horizon_end,
        scenario_name=payload.scenario_name,
        currency=result.currency,
        assumptions_json={"account_ids": payload.account_ids, "as_of": today.isoformat()},
        starting_balance=result.starting_balance,
        projected_ending_balance=result.balance_on_horizon_end,
        monthly_items=[
            ForecastMonthlyItem(
                reference_month=m.reference_month,
                projected_income=m.projected_income,
                projected_expenses=m.projected_expenses,
                projected_savings=m.projected_savings,
                projected_end_balance=m.projected_end_balance,
            )
            for m in result.monthly_summaries
        ],
    )
    db.add(forecast_run)
    db.commit()
    db.refresh(forecast_run)
    return forecast_run


@router.get("", response_model=list[ForecastRunRead])
def list_forecast_runs(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    query = (
        select(ForecastRun)
        .where(ForecastRun.user_id == profile.id)
        .options(selectinload(ForecastRun.monthly_items))
        .order_by(ForecastRun.run_at.desc())
    )
    return list(db.execute(query).scalars())


@router.get("/{run_id}", response_model=ForecastRunRead)
def get_forecast_run(run_id: int, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    forecast_run = db.get(ForecastRun, run_id)
    if forecast_run is None or forecast_run.user_id != profile.id:
        raise HTTPException(status_code=404, detail="Previsão não encontrada.")
    return forecast_run


@router.get("/savings-capacity/estimate", response_model=SavingsCapacityRead)
def savings_capacity(months: int = 12, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    today = dt.date.today()
    history = []
    cursor = today.replace(day=1)
    for _ in range(months):
        cursor = (cursor.replace(day=1) - dt.timedelta(days=1)).replace(day=1)
        start, end = month_bounds(cursor)
        totals = actual_totals(db, profile.id, start, end)
        income, expenses = convert_period_totals(db, totals, profile.base_currency, end)
        history.insert(0, realized_savings(income, expenses))

    estimate = savings_capacity_estimate(history)
    return SavingsCapacityRead(**estimate, currency=profile.base_currency)
