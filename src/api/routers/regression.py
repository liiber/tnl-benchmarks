from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.regression import (
    RegressionBaselineResponse,
    RegressionBaselineUpsertRequest,
    RegressionCompareRequest,
    RegressionCompareResponse,
)
from src.api.services.regression_service import (
    compare_runs,
    get_all_baselines,
    get_baseline_by_name,
    upsert_regression_baseline,
)
from src.database import get_async_db

router = APIRouter(prefix="/api/v1/regressions", tags=["regressions"])

DbSession = Annotated[AsyncSession, Depends(get_async_db)]


@router.get("/baselines", response_model=list[RegressionBaselineResponse])
async def list_baselines(session: DbSession) -> list[RegressionBaselineResponse]:
    return await get_all_baselines(session=session)


@router.get("/baselines/{benchmark_name}", response_model=RegressionBaselineResponse)
async def get_baseline(
    benchmark_name: str,
    session: DbSession,
) -> RegressionBaselineResponse:
    return await get_baseline_by_name(session=session, benchmark_name=benchmark_name)


@router.post("/baselines/{benchmark_name}", response_model=RegressionBaselineResponse)
async def set_regression_baseline(
    benchmark_name: str,
    payload: RegressionBaselineUpsertRequest,
    session: DbSession,
) -> RegressionBaselineResponse:
    return await upsert_regression_baseline(
        session=session,
        benchmark_name=benchmark_name,
        baseline_run_id=payload.baseline_run_id,
    )


@router.post("/compare", response_model=RegressionCompareResponse)
async def compare_regressions(
    request: RegressionCompareRequest,
    session: DbSession,
) -> RegressionCompareResponse:
    return await compare_runs(session=session, request=request)
