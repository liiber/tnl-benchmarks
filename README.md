# TNL Benchmarks

A system for automated execution, storage, and regression analysis of [TNL](https://gitlab.com/tnl-project/tnl) benchmarks.

## How it works

1. **Ingest** — clones/updates the TNL repository, builds benchmarks via `just`, runs each binary, parses results and stores them in PostgreSQL.
2. **API** — FastAPI service for querying results, managing regression baselines, and triggering ingest remotely.

## Environment setup

To run the project, the `.env` must be configured.
Here is `.env` file setup

```
# ----------------------------
# Database credentials
# ----------------------------
DB_USER=YOUR_DATABASE_USER
DB_PASSWORD=YOUR_DATABASE_PASSWORD
DB_NAME=YOUR_DATABASE_NAME
DB_HOST=YOUR_DATABASE_HOST
DB_PORT=YOUR_DATABASE_PORT

# ----------------------------
# Runtime settings
# ----------------------------
API_PORT=YOUR_API_PORT
INGEST_TRIGGER_TOKEN=YOUR_INGEST_TRIGGER_TOKEN

# ----------------------------
# TNL settings
# ----------------------------
TNL_REPO_URL=https://gitlab.com/tnl-project/tnl.git # TNL git repository URL
WORKSPACE_PATH=/workspace                           # your may differ
TNL_USE_CUDA=ON                                     # ON / OFF
TNL_USE_HIP=OFF                                     # ON / OFF
TNL_USE_MPI=OFF                                     # ON / OFF
TNL_USE_OPENMP=ON                                   # ON / OFF
TNL_CMAKE_BUILD_TYPE=Release

# Build only specific benchmark(s). Use "benchmarks" to build all.
TNL_BUILD_TARGET=benchmarks

# Run only binaries matching this prefix. Use "tnl-benchmark" for all.
TNL_BENCHMARK_NAMING_PATTERN=tnl-benchmark

# Kill any single benchmark binary after this many seconds (empty = no timeout).
TNL_BENCHMARK_TIMEOUT_SECONDS=3600
```
