from sqlalchemy import select, func
from src.models.benchmarks import BenchmarkOperation, BenchmarkResult, BenchmarkRun, Benchmark

UNKNOW_FIELD_VALUE = "UNKNOWN"

async def insert_benchmark_run(async_session, benchmark_name, machine, run_data, source_info):
    # 1. Бенчмарк
    stmt = select(Benchmark).filter_by(benchmark_name=benchmark_name)
    result = await async_session.execute(stmt)
    benchmark = result.scalar_one_or_none()

    if not benchmark:
        benchmark = Benchmark(benchmark_name=benchmark_name)
        async_session.add(benchmark)
        await async_session.commit()  # обязательно await

    # 2. Run
    run = BenchmarkRun(
        benchmark_id=benchmark.id,
        machine_id=machine.id,
        start_time=func.now(),
        end_time=func.now(),
        duration=0.0,
        source_url=source_info["url"],
        source_version=source_info["version"],
        source_checksum=source_info["checksum"]
    )
    async_session.add(run)
    await async_session.commit()

    # 3. Операции и результаты
    for r in run_data:
        stmt_op = select(BenchmarkOperation).filter_by(
            benchmark_id=benchmark.id,
            operation_name=r["operation"]
        )
        op_result = await async_session.execute(stmt_op)
        operation = op_result.scalar_one_or_none()

        if not operation:
            operation = BenchmarkOperation(
                benchmark_id=benchmark.id,
                operation_name=r["operation"]
            )
            async_session.add(operation)
            await async_session.commit()

        print(r.keys())

        result_obj = BenchmarkResult(
            operation_id=operation.id,
            run_id=run.id,
            precision=r["precision"],
            host_allocator=r.get("host allocator", UNKNOW_FIELD_VALUE),
            size=float(r.get('size', 0)),
            performer=r["performer"],
            time=float(r["time"]),
            stddev=float(r["stddev"]),
            stddev_time=float(r["stddev/time"]),
            loops=int(r["loops"]),
            bandwidth=float(r["bandwidth"])
        )
        async_session.add(result_obj)

    await async_session.commit()  # финальный коммит всех результатов
    return run
