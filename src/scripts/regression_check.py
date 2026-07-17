import argparse
import asyncio

from fastapi import HTTPException

from src.api.schemas.regression import RegressionCompareRequest
from src.api.services.regression_service import compare_runs
from src.database import async_session


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simple regression gate based on benchmark run comparisons."
    )
    parser.add_argument(
        "--benchmark",
        action="append",
        dest="benchmarks",
        help="Benchmark name to compare. Can be passed multiple times.",
    )
    parser.add_argument("--baseline-run-id", type=int, default=None)
    parser.add_argument("--target-run-id", type=int, default=None)
    parser.add_argument("--time-threshold-pct", type=float, default=5.0)
    parser.add_argument(
        "--soft-fail-on-setup-error",
        action="store_true",
        help="Return success even when baseline/setup is missing (useful for first bootstrap run).",
    )
    return parser


async def run_check(args: argparse.Namespace) -> int:
    request = RegressionCompareRequest(
        baseline_run_id=args.baseline_run_id,
        target_run_id=args.target_run_id,
        benchmarks=args.benchmarks,
        time_regression_threshold_pct=args.time_threshold_pct,
    )
    try:
        async with async_session() as session:
            report = await compare_runs(session, request)
    except HTTPException as exc:
        print(f"Regression check failed: {exc.detail}")
        return 0 if args.soft_fail_on_setup_error else 2

    print(f"has_regressions={report.has_regressions}")
    for summary in report.summaries:
        print(
            f"benchmark={summary.benchmark} "
            f"baseline={summary.baseline_run_id} "
            f"target={summary.target_run_id} "
            f"compared={summary.compared_items} "
            f"regressions={summary.regressions} "
            f"missing_in_target={summary.missing_in_target} "
            f"new_in_target={summary.new_in_target}"
        )
    return 1 if report.has_regressions else 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run_check(args)))


if __name__ == "__main__":
    main()
