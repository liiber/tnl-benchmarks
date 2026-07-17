import argparse
import asyncio

from sqlalchemy import desc, select

from src.api.services.regression_service import upsert_regression_baseline
from src.database import async_session
from src.models.benchmarks import Benchmark, BenchmarkRun


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Set/update regression baseline run.")
    parser.add_argument("--benchmark", required=True, help="Benchmark name.")
    parser.add_argument(
        "--run-id",
        type=int,
        default=None,
        help="Baseline run id. If omitted, latest run for benchmark is used.",
    )
    return parser


async def _get_latest_run_id(benchmark: str) -> int:
    async with async_session() as session:
        stmt = (
            select(BenchmarkRun.id)
            .join(Benchmark, BenchmarkRun.benchmark_id == Benchmark.id)
            .where(Benchmark.benchmark_name == benchmark)
            .order_by(desc(BenchmarkRun.start_time))
        )
        run_id = (await session.execute(stmt)).scalars().first()
        if run_id is None:
            raise RuntimeError(f"No runs found for benchmark '{benchmark}'.")
        return run_id


async def run_set(benchmark: str, run_id: int | None) -> None:
    selected_run_id = (
        run_id if run_id is not None else await _get_latest_run_id(benchmark)
    )
    async with async_session() as session:
        baseline = await upsert_regression_baseline(
            session=session,
            benchmark_name=benchmark,
            baseline_run_id=selected_run_id,
        )
    print(
        f"Baseline set: benchmark={baseline.benchmark} "
        f"baseline_run_id={baseline.baseline_run_id}"
    )


def main() -> None:
    args = build_parser().parse_args()
    asyncio.run(run_set(benchmark=args.benchmark, run_id=args.run_id))


if __name__ == "__main__":
    main()
