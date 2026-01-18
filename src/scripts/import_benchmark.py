import argparse
import hashlib
import json
from pathlib import Path
import asyncio

from src.database import async_session
from src.scripts.insert_benchmark_machine import insert_benchmark_machine
from src.scripts.insert_benchmark_run import insert_benchmark_run

repo_url = "https://gitlab.com/tnl-project/tnl"

async def main():
    parser = argparse.ArgumentParser(description="Import benchmark runs to database.")
    parser.add_argument("--metadata", type=str, required=True, help="Your <benchmark-name>.metadata.json file")
    parser.add_argument("--run", type=str, required=True, help="Your <benchmark-name>.log file")
    args = parser.parse_args()

    metadata_path = Path(args.metadata)
    run_path = Path(args.run)

    benchmark_name = metadata_path.stem.replace(".metadata", "")

    checksum = hashlib.sha256(metadata_path.read_bytes()).hexdigest()

    source_info = {
        "url": repo_url,
        "version": "0.0.0-test", # during local testing
        "checksum": checksum
    }

    with metadata_path.open() as f:
        machine_meta = json.load(f)

    with run_path.open() as f:
        run_data = [json.loads(line) for line in f]

    async with async_session() as session:
        machine = await insert_benchmark_machine(session, machine_meta)
        run = await insert_benchmark_run(session, benchmark_name, machine, run_data, source_info)

    print(f"Benchmark '{benchmark_name}' imported successfully.")
    print(f"Source info: {source_info}")


if __name__ == "__main__":
    asyncio.run(main())
