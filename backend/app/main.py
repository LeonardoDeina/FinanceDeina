from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.accounts.router import router as accounts_router
from app.backup.router import router as backup_router
from app.budgets.router import router as budgets_router
from app.categories.router import router as categories_router
from app.closings.router import router as closings_router
from app.core.config import get_settings
from app.currency.exceptions import MissingExchangeRateError
from app.currency.router import router as currency_router
from app.currency.seed import seed_default_currencies
from app.db.session import SessionLocal
from app.forecasting.router import router as forecasting_router
from app.recurring.router import router as recurring_router
from app.reports.router import router as reports_router
from app.transactions.router import router as transactions_router
from app.users.router import router as users_router

settings = get_settings()

app = FastAPI(title="FinanceDeina API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    users_router,
    currency_router,
    accounts_router,
    categories_router,
    transactions_router,
    recurring_router,
    budgets_router,
    forecasting_router,
    closings_router,
    reports_router,
    backup_router,
):
    app.include_router(router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def on_startup() -> None:
    db = SessionLocal()
    try:
        seed_default_currencies(db)
    finally:
        db.close()


@app.exception_handler(MissingExchangeRateError)
def missing_rate_handler(_request: Request, exc: MissingExchangeRateError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
