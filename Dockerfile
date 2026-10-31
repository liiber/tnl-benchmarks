# CUDA devel image so TNL can be built with GPU support (provides nvcc + CUDA libs).
# 12.8 is the first CUDA release that supports Blackwell (sm_120 / RTX 50xx).
FROM nvidia/cuda:12.8.0-devel-ubuntu24.04

# Pinned uv version (keep in sync with the one used locally / in CI).
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    # uv-managed Python (version from .python-version), not the distro one.
    UV_PYTHON_INSTALL_DIR=/opt/python \
    # The venv lives outside /app: docker-compose bind-mounts the source over
    # /app, which would otherwise hide the venv (or replace it with the host's).
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # CMake comes from PyPI (>=3.30 required by TNL; ubuntu 24.04 apt only ships 3.28).
    UV_TOOL_DIR=/opt/uv-tools \
    UV_TOOL_BIN_DIR=/usr/local/bin \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ninja-build \
    build-essential \
    ca-certificates \
    curl \
    libblas-dev \
    liblapack-dev \
    libopenblas-dev \
    libtbb-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

RUN --mount=type=cache,target=/root/.cache/uv \
    uv tool install "cmake>=3.30"

# Dependencies first, in their own layer: code changes don't reinstall them.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-dev

COPY . .

# TNL's CUDA benchmarks require NVIDIA CCCL (Thrust/CUB); it ships with the CUDA
# toolkit but is not on cmake's default search path, so point find_package(CCCL) at it.
ENV CCCL_DIR=/usr/local/cuda-12.8/targets/x86_64-linux/lib/cmake/cccl

CMD ["python", "-m", "src.main"]
