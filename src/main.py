import asyncio
from src.database import init_db
from src.models.benchmarks import Benchmark, BenchmarkOperation, BenchmarkRun, BenchmarkMachine, BenchmarkResult
from src.ingest.ingest import benchmark_ingest_runner

async def wait_for_db():
    for i in range(10):
        try:
            await init_db()
            return
        except Exception as e:
            print(f"Database not ready ({i+1}/10): {e}")
            await asyncio.sleep(2)
    raise RuntimeError("Database failed to start")

async def main():
    print("Initializing database...")
    await wait_for_db()
    print("Database initialized!")

    await benchmark_ingest_runner()

asyncio.run(main())