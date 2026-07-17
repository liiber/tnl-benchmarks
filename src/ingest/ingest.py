import json
import os
import shlex
import subprocess
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.database import async_session
from src.environment import ENV
from src.ingest.mappers import build_machine_fields
from src.ingest.parsers import parse_log, parse_metadata
from src.ingest.utils import (
    TNL_REPO_PATH,
    TNL_REPO_URL,
    WORKSPACE_PATH,
    build_tnl,
    compute_machine_hash,
    compute_run_hash,
    get_git_commit_hash,
    get_or_create,
    git_clone_or_pull,
    run_command,
)
from src.models.benchmarks import (
    Benchmark,
    BenchmarkMachine,
    BenchmarkOperation,
    BenchmarkResult,
    BenchmarkResultMetadata,
    BenchmarkRun,
)
from src.utils import Logger, utcnow

TNL_BENCHMARKS_BUILD_OUTPUT_DIR = f"{TNL_REPO_PATH}/build/bin"
BENCHMARK_METADATA_FILE_SUFFIX = ".metadata.json"
BENCHMARK_LOG_FILE_SUFFIX = ".log"
BENCHMARK_ARGS_FILE = "benchmark-args.json"


def _load_benchmark_args() -> dict[str, list[str]]:
    if not os.path.exists(BENCHMARK_ARGS_FILE):
        return {}
    with open(BENCHMARK_ARGS_FILE) as f:
        raw = json.load(f)
    return {name: shlex.split(args) for name, args in raw.items()}


def run_benchmarks(execute: bool = True) -> dict[str, list[tuple[str, str]]]:
    results: dict[str, list[tuple[str, str]]] = {}

    per_benchmark_args = _load_benchmark_args()
    timeout = ENV.TNL_BENCHMARK_TIMEOUT_SECONDS

    for root, _dirs, files in os.walk(TNL_BENCHMARKS_BUILD_OUTPUT_DIR):
        for file in sorted(files):
            if not file.startswith(ENV.TNL_BENCHMARK_NAMING_PATTERN):
                continue
            if file.endswith(BENCHMARK_METADATA_FILE_SUFFIX) or file.endswith(
                BENCHMARK_LOG_FILE_SUFFIX
            ):
                continue

            if execute:
                binary = os.path.join(root, file)
                cmd = [binary] + per_benchmark_args.get(file, [])
                timeout_str = f" (timeout={timeout}s)" if timeout else ""
                Logger.info(f">> Running: {file}{timeout_str}")

                try:
                    run_command(cmd, cwd=root, timeout=timeout)
                except subprocess.TimeoutExpired:
                    Logger.warning(f">> Timed out after {timeout}s: {file}, skipping")
                    continue
                except Exception as exc:
                    Logger.error(f">> Failed: {file}: {exc}")
                    continue
            else:
                Logger.info(f">> Collecting existing results: {file}")

            metadata = os.path.join(root, f"{file}{BENCHMARK_METADATA_FILE_SUFFIX}")
            log = os.path.join(root, f"{file}{BENCHMARK_LOG_FILE_SUFFIX}")
            if not os.path.exists(metadata) or not os.path.exists(log):
                Logger.warning(f">> Missing output files for {file}, skipping")
                continue

            results.setdefault(file, []).append((metadata, log))

    return results


async def ingest_results(
    benchmark_name: str,
    files: list[tuple[str, str]],
    start_time: datetime,
    end_time: datetime,
    commit_hash: str,
):
    if not files:
        Logger.warning(f">> [{benchmark_name}] No results found, skipping")
        return

    all_rows = []
    for _metadata_path, log_path in files:
        all_rows.extend(row for row in parse_log(log_path) if row["operation"])

    if not all_rows:
        Logger.warning(f">> [{benchmark_name}] No operations found, skipping")
        return

    async with async_session() as session:
        async with session.begin():
            metadata = parse_metadata(files[0][0])
            machine_hash = compute_machine_hash(metadata)
            run_hash = compute_run_hash(
                commit_hash,
                machine_hash,
                start_time.isoformat(),
                benchmark_name,
            )

            Logger.info(
                f">> [{benchmark_name}] commit={commit_hash[:8]} run_hash={run_hash[:8]}"
            )

            existing = await session.execute(
                select(BenchmarkRun).where(BenchmarkRun.run_hash == run_hash)
            )
            if existing.scalar_one_or_none():
                Logger.warning(f">> [{benchmark_name}] Run already exists, skipping")
                return

            benchmark = await get_or_create(
                session,
                Benchmark,
                benchmark_name=benchmark_name,
            )

            machine = await get_or_create(
                session,
                BenchmarkMachine,
                machine_hash=machine_hash,
                defaults=build_machine_fields(metadata),
            )

            run = BenchmarkRun(
                benchmark_id=benchmark.id,
                machine_id=machine.id,
                run_hash=run_hash,
                source_url=TNL_REPO_URL,
                source_version=commit_hash,
                start_time=start_time,
                end_time=start_time,
                duration=0,
            )

            session.add(run)
            await session.flush()

            operations_cache = {}

            for row in all_rows:
                op_name = row["operation"]

                if op_name not in operations_cache:
                    op = await get_or_create(
                        session,
                        BenchmarkOperation,
                        benchmark_id=benchmark.id,
                        operation_name=op_name,
                    )
                    operations_cache[op_name] = op
                else:
                    op = operations_cache[op_name]

                metrics = row["metrics"]
                result = BenchmarkResult(
                    operation_id=op.id,
                    run_id=run.id,
                    time=metrics["time"],
                    time_median=metrics["time_median"],
                    stddev=metrics["stddev"],
                    stddev_time=metrics["stddev_time"],
                    loops=metrics["loops"],
                    bandwidth=metrics["bandwidth"],
                    cpu_cycles=metrics["cpu_cycles"],
                    cpu_cycles_median=metrics["cpu_cycles_median"],
                    cpu_cycles_stddev=metrics["cpu_cycles_stddev"],
                    cpu_cycles_per_operation=metrics["cpu_cycles_per_operation"],
                    ops_per_loop=metrics["ops_per_loop"],
                    metadata_entries=[
                        BenchmarkResultMetadata(key=k, value=v)
                        for k, v in row["metadata"].items()
                    ],
                )

                session.add(result)

            run.end_time = end_time
            run.duration = (end_time - start_time).total_seconds()

        try:
            await session.commit()
            Logger.success(f">> [{benchmark_name}] Ingest completed")
        except IntegrityError:
            await session.rollback()
            Logger.error(f">> [{benchmark_name}] Duplicate detected (race condition)")


async def benchmark_ingest_runner(
    prepare_sources: bool = True, execute_benchmarks: bool = True
):
    os.makedirs(WORKSPACE_PATH, exist_ok=True)

    if not execute_benchmarks:
        Logger.error("=" * 64)
        Logger.error(">> DANGER: running in --no-rebuild mode.")
        Logger.error(">> Benchmarks are NOT executed. Existing .log/.metadata.json")
        Logger.error(">> files on disk are ingested as-is, so the data may be STALE")
        Logger.error(
            ">> or from a previous commit/build. Do NOT use for fresh results."
        )
        Logger.error("=" * 64)

    if prepare_sources:
        git_clone_or_pull()
        build_tnl()

    commit_hash = get_git_commit_hash()
    start_time = utcnow()
    results = run_benchmarks(execute=execute_benchmarks)
    end_time = utcnow()

    if not results:
        Logger.warning(">> No benchmark results found")
        return

    for benchmark_name, files in results.items():
        await ingest_results(benchmark_name, files, start_time, end_time, commit_hash)
