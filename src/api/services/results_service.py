from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.results import (
    BenchmarkResultResponse,
    BenchmarkResultsFilterRequest,
    BenchmarkResultsPage,
)
from src.api.services.metadata_filters import metadata_value_filter
from src.models.benchmarks import (
    Benchmark,
    BenchmarkMachine,
    BenchmarkOperation,
    BenchmarkResult,
    BenchmarkResultMetadata,
    BenchmarkRun,
)


def _apply_filters(stmt: Select, filters: BenchmarkResultsFilterRequest) -> Select:
    if filters.date_from is not None:
        stmt = stmt.where(BenchmarkRun.start_time >= filters.date_from)
    if filters.date_to is not None:
        stmt = stmt.where(BenchmarkRun.end_time <= filters.date_to)
    if filters.benchmarks:
        stmt = stmt.where(Benchmark.benchmark_name.in_(filters.benchmarks))
    if filters.operations:
        stmt = stmt.where(BenchmarkOperation.operation_name.in_(filters.operations))
    if filters.performers:
        stmt = stmt.where(
            BenchmarkResult.id.in_(
                metadata_value_filter("performer", filters.performers)
            )
        )
    if filters.precisions:
        stmt = stmt.where(
            BenchmarkResult.id.in_(
                metadata_value_filter("precision", filters.precisions)
            )
        )
    return stmt


def _base_join() -> Select:
    return (
        select()
        .join(BenchmarkRun, BenchmarkResult.run_id == BenchmarkRun.id)
        .join(Benchmark, BenchmarkRun.benchmark_id == Benchmark.id)
        .join(BenchmarkOperation, BenchmarkResult.operation_id == BenchmarkOperation.id)
        .join(BenchmarkMachine, BenchmarkRun.machine_id == BenchmarkMachine.id)
        .select_from(BenchmarkResult)
    )


def build_results_query(filters: BenchmarkResultsFilterRequest) -> Select:
    stmt = _base_join().add_columns(
        Benchmark.benchmark_name.label("benchmark"),
        BenchmarkOperation.operation_name.label("operation"),
        BenchmarkRun.id.label("run_id"),
        BenchmarkRun.run_hash,
        BenchmarkRun.start_time,
        BenchmarkRun.end_time,
        BenchmarkRun.duration,
        BenchmarkRun.source_version,
        BenchmarkMachine.host_name.label("machine"),
        BenchmarkResult.id.label("result_id"),
        BenchmarkResult.time,
        BenchmarkResult.time_median,
        BenchmarkResult.stddev,
        BenchmarkResult.stddev_time,
        BenchmarkResult.loops,
        BenchmarkResult.bandwidth,
        BenchmarkResult.cpu_cycles,
        BenchmarkResult.cpu_cycles_median,
        BenchmarkResult.cpu_cycles_stddev,
        BenchmarkResult.cpu_cycles_per_operation,
        BenchmarkResult.ops_per_loop,
    )
    stmt = _apply_filters(stmt, filters)
    return (
        stmt.order_by(BenchmarkRun.start_time.desc())
        .limit(filters.limit)
        .offset(filters.offset)
    )


def build_count_query(filters: BenchmarkResultsFilterRequest) -> Select:
    stmt = _base_join().add_columns(func.count().label("total"))
    return _apply_filters(stmt, filters)


async def get_benchmark_results(
    session: AsyncSession, filters: BenchmarkResultsFilterRequest
) -> BenchmarkResultsPage:
    total = (await session.execute(build_count_query(filters))).scalar_one()
    rows = (await session.execute(build_results_query(filters))).mappings().all()

    result_ids = [r["result_id"] for r in rows]
    meta_by_result: dict[int, dict[str, str | None]] = {}
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

    items = [
        BenchmarkResultResponse(
            **{k: v for k, v in r.items() if k != "result_id"},
            metadata=meta_by_result.get(r["result_id"], {}),
        )
        for r in rows
    ]

    return BenchmarkResultsPage(
        total=total,
        limit=filters.limit,
        offset=filters.offset,
        items=items,
    )
