from collections.abc import Iterable
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.regression import (
    RegressionBaselineResponse,
    RegressionCompareRequest,
    RegressionCompareResponse,
    RegressionItemResponse,
    RegressionRunSummary,
)
from src.api.services.metadata_filters import metadata_value_filter
from src.models.benchmarks import (
    Benchmark,
    BenchmarkOperation,
    BenchmarkResult,
    BenchmarkResultMetadata,
    BenchmarkRun,
)
from src.models.regression import RegressionBaseline


@dataclass
class _RunMetricRow:
    result_id: int
    operation: str
    time: float
    metadata: dict[str, str | None]


def _metric_key(row: _RunMetricRow) -> tuple:
    return (row.operation,) + tuple(sorted(row.metadata.items()))


def _percentage_change(current: float | None, baseline: float | None) -> float | None:
    if baseline in (None, 0) or current is None:
        return None
    return ((current - baseline) / baseline) * 100.0


def _classify_change(
    time_change_pct: float | None, threshold: float
) -> tuple[bool, bool]:
    """Classify a relative time change as a regression and/or an improvement.

    A positive change beyond ``threshold`` is a regression (the operation became
    slower); a negative change beyond ``threshold`` is an improvement (faster). A value
    within the band, or ``None``, is neither. The two flags are mutually exclusive.
    """
    is_regression = time_change_pct is not None and time_change_pct > threshold
    is_improvement = (
        not is_regression
        and time_change_pct is not None
        and time_change_pct < -threshold
    )
    return is_regression, is_improvement


async def _get_run(session: AsyncSession, run_id: int) -> BenchmarkRun:
    run = await session.get(BenchmarkRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} was not found.")
    return run


async def _get_benchmark_name(session: AsyncSession, benchmark_id: int) -> str:
    benchmark = await session.get(Benchmark, benchmark_id)
    if benchmark is None:
        raise HTTPException(
            status_code=404, detail=f"Benchmark {benchmark_id} was not found."
        )
    return benchmark.benchmark_name


async def get_all_baselines(session: AsyncSession) -> list[RegressionBaselineResponse]:
    rows = (await session.execute(select(RegressionBaseline))).scalars().all()
    return [
        RegressionBaselineResponse(
            benchmark=b.benchmark_name,
            baseline_run_id=b.baseline_run_id,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )
        for b in rows
    ]


async def get_baseline_by_name(
    session: AsyncSession, benchmark_name: str
) -> RegressionBaselineResponse:
    baseline = (
        await session.execute(
            select(RegressionBaseline).where(
                RegressionBaseline.benchmark_name == benchmark_name
            )
        )
    ).scalar_one_or_none()
    if baseline is None:
        raise HTTPException(
            status_code=404,
            detail=f"Baseline for benchmark '{benchmark_name}' was not found.",
        )
    return RegressionBaselineResponse(
        benchmark=baseline.benchmark_name,
        baseline_run_id=baseline.baseline_run_id,
        created_at=baseline.created_at,
        updated_at=baseline.updated_at,
    )


async def upsert_regression_baseline(
    session: AsyncSession, benchmark_name: str, baseline_run_id: int
) -> RegressionBaselineResponse:
    run = await _get_run(session, baseline_run_id)
    run_benchmark_name = await _get_benchmark_name(session, run.benchmark_id)
    if run_benchmark_name != benchmark_name:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Run {baseline_run_id} belongs to benchmark '{run_benchmark_name}', "
                f"not '{benchmark_name}'."
            ),
        )

    existing = await session.execute(
        select(RegressionBaseline).where(
            RegressionBaseline.benchmark_name == benchmark_name
        )
    )
    baseline = existing.scalar_one_or_none()
    if baseline is None:
        baseline = RegressionBaseline(
            benchmark_name=benchmark_name,
            baseline_run_id=baseline_run_id,
        )
        session.add(baseline)
    else:
        baseline.baseline_run_id = baseline_run_id

    await session.commit()
    await session.refresh(baseline)
    return RegressionBaselineResponse(
        benchmark=baseline.benchmark_name,
        baseline_run_id=baseline.baseline_run_id,
        created_at=baseline.created_at,
        updated_at=baseline.updated_at,
    )


async def _get_baseline_run_id(session: AsyncSession, benchmark_name: str) -> int:
    baseline = (
        await session.execute(
            select(RegressionBaseline).where(
                RegressionBaseline.benchmark_name == benchmark_name
            )
        )
    ).scalar_one_or_none()
    if baseline is None:
        raise HTTPException(
            status_code=404,
            detail=f"Baseline for benchmark '{benchmark_name}' was not found.",
        )
    return baseline.baseline_run_id


async def _get_latest_run_id(
    session: AsyncSession, benchmark_name: str, exclude_run_id: int | None = None
) -> int:
    stmt = (
        select(BenchmarkRun.id)
        .join(Benchmark, BenchmarkRun.benchmark_id == Benchmark.id)
        .where(Benchmark.benchmark_name == benchmark_name)
        .order_by(desc(BenchmarkRun.start_time))
    )
    if exclude_run_id is not None:
        stmt = stmt.where(BenchmarkRun.id != exclude_run_id)
    run_id = (await session.execute(stmt)).scalars().first()
    if run_id is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not determine target run for benchmark '{benchmark_name}'.",
        )
    return run_id


async def _fetch_run_metrics(
    session: AsyncSession,
    run_id: int,
    operations: Iterable[str] | None,
    performers: Iterable[str] | None,
    precisions: Iterable[str] | None,
) -> list[_RunMetricRow]:
    stmt = (
        select(
            BenchmarkResult.id.label("result_id"),
            BenchmarkOperation.operation_name.label("operation"),
            BenchmarkResult.time.label("time"),
        )
        .join(BenchmarkOperation, BenchmarkResult.operation_id == BenchmarkOperation.id)
        .where(BenchmarkResult.run_id == run_id)
    )
    if operations:
        stmt = stmt.where(BenchmarkOperation.operation_name.in_(operations))
    if performers:
        stmt = stmt.where(
            BenchmarkResult.id.in_(metadata_value_filter("performer", performers))
        )
    if precisions:
        stmt = stmt.where(
            BenchmarkResult.id.in_(metadata_value_filter("precision", precisions))
        )

    result_rows = (await session.execute(stmt)).all()

    meta_by_result: dict[int, dict[str, str | None]] = {}
    result_ids = [r.result_id for r in result_rows]
    if result_ids:
        meta_rows = (
            (
                await session.execute(
                    select(BenchmarkResultMetadata).where(
                        BenchmarkResultMetadata.result_id.in_(result_ids)
                    )
                )
            )
            .scalars()
            .all()
        )
        for m in meta_rows:
            meta_by_result.setdefault(m.result_id, {})[m.key] = m.value

    return [
        _RunMetricRow(
            result_id=r.result_id,
            operation=r.operation,
            time=r.time,
            metadata=meta_by_result.get(r.result_id, {}),
        )
        for r in result_rows
    ]


async def _compare_benchmark(
    session: AsyncSession,
    benchmark_name: str,
    request: RegressionCompareRequest,
) -> tuple[list[RegressionItemResponse], RegressionRunSummary]:
    """Compare one benchmark's target run against its baseline run.

    Resolves the baseline and target runs, matches results by composite key, and
    returns the per-operation items together with the aggregate summary.
    """
    baseline_run_id = request.baseline_run_id
    if baseline_run_id is None:
        baseline_run_id = await _get_baseline_run_id(session, benchmark_name)

    target_run_id = request.target_run_id
    if target_run_id is None:
        target_run_id = await _get_latest_run_id(
            session, benchmark_name, exclude_run_id=baseline_run_id
        )

    baseline_rows = await _fetch_run_metrics(
        session,
        baseline_run_id,
        request.operations,
        request.performers,
        request.precisions,
    )
    target_rows = await _fetch_run_metrics(
        session,
        target_run_id,
        request.operations,
        request.performers,
        request.precisions,
    )

    baseline_map = {_metric_key(row): row for row in baseline_rows}
    target_map = {_metric_key(row): row for row in target_rows}

    matching_keys = baseline_map.keys() & target_map.keys()
    missing_in_target = baseline_map.keys() - target_map.keys()
    new_in_target = target_map.keys() - baseline_map.keys()

    items: list[RegressionItemResponse] = []
    regressions = 0
    improvements = 0
    for key in matching_keys:
        base = baseline_map[key]
        current = target_map[key]

        time_change_pct = _percentage_change(current.time, base.time)
        is_regression, is_improvement = _classify_change(
            time_change_pct, request.time_regression_threshold_pct
        )

        if is_regression:
            regressions += 1
        if is_improvement:
            improvements += 1

        items.append(
            RegressionItemResponse(
                benchmark=benchmark_name,
                operation=key[0],
                metadata=dict(key[1:]),
                baseline_run_id=baseline_run_id,
                target_run_id=target_run_id,
                baseline_time=base.time,
                target_time=current.time,
                time_change_pct=time_change_pct,
                is_regression=is_regression,
                is_improvement=is_improvement,
            )
        )

    summary = RegressionRunSummary(
        benchmark=benchmark_name,
        baseline_run_id=baseline_run_id,
        target_run_id=target_run_id,
        compared_items=len(matching_keys),
        regressions=regressions,
        improvements=improvements,
        missing_in_target=len(missing_in_target),
        new_in_target=len(new_in_target),
        missing_operations=sorted({k[0] for k in missing_in_target}),
        new_operations=sorted({k[0] for k in new_in_target}),
    )
    return items, summary


async def compare_runs(
    session: AsyncSession, request: RegressionCompareRequest
) -> RegressionCompareResponse:
    benchmark_names = request.benchmarks

    if request.baseline_run_id is not None:
        baseline_run = await _get_run(session, request.baseline_run_id)
        baseline_benchmark_name = await _get_benchmark_name(
            session, baseline_run.benchmark_id
        )
        if benchmark_names and baseline_benchmark_name not in benchmark_names:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Run {request.baseline_run_id} belongs to benchmark "
                    f"'{baseline_benchmark_name}', not requested benchmarks."
                ),
            )
        benchmark_names = [baseline_benchmark_name]

    if not benchmark_names:
        benchmark_rows = (
            (await session.execute(select(RegressionBaseline.benchmark_name)))
            .scalars()
            .all()
        )
        benchmark_names = list(benchmark_rows)
    if not benchmark_names:
        raise HTTPException(
            status_code=400,
            detail=(
                "No benchmarks selected and no configured baselines found. "
                "Set a baseline first or provide benchmarks."
            ),
        )

    items: list[RegressionItemResponse] = []
    summaries: list[RegressionRunSummary] = []

    for benchmark_name in benchmark_names:
        benchmark_items, summary = await _compare_benchmark(
            session, benchmark_name, request
        )
        items.extend(benchmark_items)
        summaries.append(summary)

    return RegressionCompareResponse(
        has_regressions=any(summary.regressions > 0 for summary in summaries),
        summaries=summaries,
        items=items,
    )
