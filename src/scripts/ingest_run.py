import argparse
import asyncio

from src.database import wait_for_db
from src.ingest.ingest import benchmark_ingest_runner
from src.utils import Logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run benchmark ingest pipeline.")
    parser.add_argument(
        "--skip-prepare",
        action="store_true",
        help="Skip git clone/pull and benchmark build step, run only binaries already built.",
    )
    parser.add_argument(
        "--no-rebuild",
        action="store_true",
        help=(
            "Ingest the .log/.metadata.json files already on disk WITHOUT building "
            "or running benchmarks. Fast, but the data may be stale."
        ),
    )
    return parser


async def run_ingest(skip_prepare: bool, no_rebuild: bool) -> None:
    Logger.info("Initializing database...")
    await wait_for_db()
    Logger.success("Database initialized!")
    await benchmark_ingest_runner(
        prepare_sources=not (skip_prepare or no_rebuild),
        execute_benchmarks=not no_rebuild,
    )


def main() -> None:
    args = build_parser().parse_args()
    asyncio.run(run_ingest(skip_prepare=args.skip_prepare, no_rebuild=args.no_rebuild))


if __name__ == "__main__":
    main()
