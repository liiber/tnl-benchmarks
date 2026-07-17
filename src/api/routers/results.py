from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.results import BenchmarkResultsFilterRequest, BenchmarkResultsPage
from src.api.services.results_service import get_benchmark_results
from src.database import get_async_db

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_async_db)]


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/results", response_model=BenchmarkResultsPage)
async def list_benchmark_results(
    filters: BenchmarkResultsFilterRequest,
    session: DbSession,
) -> BenchmarkResultsPage:
    return await get_benchmark_results(session, filters)
