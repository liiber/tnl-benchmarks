import argparse
import asyncio

from src.database import wait_for_db
from src.ingest.ingest import benchmark_ingest_runner
from src.utils import Logger


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TNL benchmark ingest pipeline.")
    parser.add_argument(
        "--skip-prepare",
        action="store_true",
        help="Skip git clone/pull and build; run the already-built binaries.",
    )
    parser.add_argument(
        "--no-rebuild",
        action="store_true",
        help=(
            "Ingest the .log/.metadata.json files already on disk WITHOUT building "
            "or running benchmarks. Fast, but the data may be stale."
        ),
    )
    return parser.parse_args()


async def main(skip_prepare: bool, no_rebuild: bool) -> None:
    Logger.bold("=== TNL Benchmarks Ingest ===")
    Logger.info("Initializing database...")
    await wait_for_db()
    Logger.success("Database initialized!")
    await benchmark_ingest_runner(
        prepare_sources=not (skip_prepare or no_rebuild),
        execute_benchmarks=not no_rebuild,
    )
    Logger.bold("=== Done ===")


_args = _parse_args()
asyncio.run(main(skip_prepare=_args.skip_prepare, no_rebuild=_args.no_rebuild))
