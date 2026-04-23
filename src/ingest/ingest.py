import os
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from src.database import async_session
from src.models.benchmarks import (
    Benchmark,
    BenchmarkOperation,
    BenchmarkRun,
    BenchmarkMachine,
    BenchmarkResult,
)
from src.ingest.utils import (
    TNL_REPO_PATH,
    TNL_REPO_URL,
    get_git_commit_hash,
    run_command,
    build_tnl,
    WORKSPACE_PATH,
    git_clone_or_pull,
    sha256_folder,
    compute_machine_hash,
    compute_run_hash,
    get_or_create,
)

TNL_BENCHMARKS_BUILD_OUTPUT_DIR = f"{TNL_REPO_PATH}/build/bin" # Benchmarks are build to `bin` folder
TNL_BENCHMARK_METADATA_FILE_FORMAT=".metadata.json"
TNL_BENCHMARK_LOG_FILE_FORMAT= ".log"
TNL_BENCHMARK_NAMING_PATTERN="tnl-benchmark-blas" # TODO: Rename to "tnl-benchmark"

def parse_metadata(path: str):
    with open(path) as f:
        return json.load(f)

def parse_log(path: str):
    results = []

    with open(path) as f:
        for line in f:
            line = line.strip()

            if not line.startswith("{"):
                continue

            row = json.loads(line)

            results.append({
                "operation": row.get("operation") or None,
                "precision": row.get("precision") or None,
                "host_allocator": row.get("host allocator") or None,
                "size": float(row["size"]) if row.get("size") is not None else None,
                "rows": int(row["rows"]) if row.get("rows") is not None else None,
                "columns": int(row["columns"]) if row.get("columns") is not None else None,
                "performer": row.get("performer") or None,
                "time": float(row.get("time", 0)),
                "stddev": float(row.get("stddev", 0)),
                "stddev_time": float(row.get("stddev/time", 0)),
                "loops": int(row.get("loops", 0)),
                "bandwidth": float(row["bandwidth"])
                if row.get("bandwidth") not in [None, "N/A"]
                else None,
                "speedup": float(row["speedup"])
                if row.get("speedup") not in [None, "N/A"]
                else None,
            })

    return results

def run_benchmarks():
    results = []

    for root, dirs, files in os.walk(TNL_BENCHMARKS_BUILD_OUTPUT_DIR):
        for file in files:
            if file.startswith(TNL_BENCHMARK_NAMING_PATTERN) and not file.endswith(TNL_BENCHMARK_METADATA_FILE_FORMAT) and not file.endswith(TNL_BENCHMARK_LOG_FILE_FORMAT):
                binary = os.path.join(root, file)
                print(">> Running:", binary)

                run_command([binary], cwd=root)

                metadata = os.path.join(root, f"{file}.metadata.json")
                log = os.path.join(root, f"{file}.log")

                results.append((metadata, log))

    return results


async def ingest_results(files, start_time: datetime, end_time: datetime):
    if not files:
        print(">> No benchmark results found")
        return

    _METADATA_START_TIME_FORMAT = "%a %b %d %Y, %H:%M:%S"


    async with async_session() as session:
        async with session.begin():

            metadata = parse_metadata(files[0][0])
            machine_hash = compute_machine_hash(metadata)
            commit_hash = get_git_commit_hash()
            run_hash = compute_run_hash(commit_hash, machine_hash)

            raw_start = metadata.get("start time")
            if raw_start:
                try:
                    start_time = datetime.strptime(raw_start, _METADATA_START_TIME_FORMAT)
                except ValueError:
                    pass  # keep the passed-in start_time as fallback

            print(f">> commit={commit_hash[:8]}")
            print(f">> machine_hash={machine_hash[:8]}")
            print(f">> run_hash={run_hash[:8]}")

            existing = await session.execute(
                select(BenchmarkRun).where(BenchmarkRun.run_hash == run_hash)
            )
            if existing.scalar_one_or_none():
                print(">> Run already exists, skipping")
                return

            benchmark = await get_or_create(
                session,
                Benchmark,
                benchmark_name=TNL_BENCHMARK_NAMING_PATTERN
            )

            machine = await get_or_create(
                session,
                BenchmarkMachine,
                machine_hash=machine_hash,
                defaults={
                    "cpu_cache_sizes": metadata.get("CPU cache sizes (L1d, L1i, L2, L3) (kiB)") or None,
                    "cpu_cores": int(metadata.get("CPU cores", 0)),
                    "cpu_max_frequency": int(float(metadata.get("CPU max frequency (MHz)", 0))),
                    "cpu_model_name": metadata.get("CPU model name", "").strip() or None,
                    "cpu_threads_per_core": int(metadata.get("CPU threads per core", 0)),
                    "gpu_name": metadata.get("GPU name", "").strip() or None,
                    "gpu_cuda_cores": int(metadata["GPU CUDA cores"])
                    if metadata.get("GPU CUDA cores") not in [None, "", "0", 0]
                    else None,
                    "gpu_architecture": float(metadata["GPU architecture"])
                    if metadata.get("GPU architecture") not in [None, "", "0", "0.0", 0]
                    else None,
                    "gpu_clock_rate_mhz": float(metadata["GPU clock rate (MHz)"])
                    if metadata.get("GPU clock rate (MHz)") not in [None, "", "0", "0.0", 0]
                    else None,
                    "gpu_global_memory_gb": float(metadata["GPU global memory (GB)"])
                    if metadata.get("GPU global memory (GB)") not in [None, "", "0", "0.0", 0]
                    else None,
                    "gpu_memory_ecc_enabled": bool(int(metadata["GPU memory ECC enabled"]))
                    if metadata.get("GPU memory ECC enabled") not in [None, ""]
                    else None,
                    "gpu_memory_clock_rate_mhz": float(metadata["GPU memory clock rate (MHz)"])
                    if metadata.get("GPU memory clock rate (MHz)") not in [None, "", "0", "0.0", 0]
                    else None,
                    "openmp_enabled": metadata.get("OpenMP enabled", "no") == "yes",
                    "openmp_threads": int(metadata.get("OpenMP threads", 0)),
                    "architecture": metadata.get("architecture") or None,
                    "host_name": metadata.get("host name") or None,
                    "system": metadata.get("system") or None,
                    "system_release": metadata.get("system release") or None,
                }
            )

            source_checksum = sha256_folder(TNL_BENCHMARKS_BUILD_OUTPUT_DIR)

            run = BenchmarkRun(
                benchmark_id=benchmark.id,
                machine_id=machine.id,
                run_hash=run_hash,
                source_url=TNL_REPO_URL,
                source_version=commit_hash,
                source_checksum=source_checksum,
                start_time=start_time,
                end_time=start_time,
                duration=0,
            )

            session.add(run)
            await session.flush()

            operations_cache = {}

            for metadata_path, log_path in files:
                parsed = parse_log(log_path)

                for row in parsed:
                    op_name = row["operation"]

                    if not op_name:
                        print(f">> Skipping row with missing operation in {log_path}")
                        continue

                    if op_name not in operations_cache:
                        op = await get_or_create(
                            session,
                            BenchmarkOperation,
                            benchmark_id=benchmark.id,
                            operation_name=op_name
                        )
                        operations_cache[op_name] = op
                    else:
                        op = operations_cache[op_name]

                    result = BenchmarkResult(
                        operation_id=op.id,
                        run_id=run.id,
                        precision=row["precision"],
                        host_allocator=row["host_allocator"],
                        size=row["size"],
                        rows=row["rows"],
                        columns=row["columns"],
                        performer=row["performer"],
                        time=row["time"],
                        stddev=row["stddev"],
                        stddev_time=row["stddev_time"],
                        loops=row["loops"],
                        bandwidth=row["bandwidth"],
                        speedup=row["speedup"],
                    )

                    session.add(result)

            run.end_time = end_time
            run.duration = (end_time - start_time).total_seconds()

        try:
            await session.commit()
            print(">> Ingest completed")
        except IntegrityError:
            await session.rollback()
            print(">> Duplicate detected (race condition)")

async def benchmark_ingest_runner():
    os.makedirs(WORKSPACE_PATH, exist_ok=True)

    git_clone_or_pull()
    build_tnl()

    start_time = datetime.utcnow()
    results = run_benchmarks()
    end_time = datetime.utcnow()

    await ingest_results(results, start_time, end_time)