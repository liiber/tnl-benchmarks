import asyncio
from src.database import init_db
from src.models.benchmarks import Benchmark, BenchmarkOperation, BenchmarkRun, BenchmarkMachine, BenchmarkResult

async def main():
    print("Initializing database...")
    await init_db()
    print("Database initialized!")

asyncio.run(main())
