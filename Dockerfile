# CUDA devel image so TNL can be built with GPU support (provides nvcc + CUDA libs).
# 12.8 is the first CUDA release that supports Blackwell (sm_120 / RTX 50xx).
# CMake comes from pip (>=3.30 required by TNL; ubuntu 24.04 apt only ships 3.28).
FROM nvidia/cuda:12.8.0-devel-ubuntu24.04

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    ninja-build \
    build-essential \
    curl \
    libblas-dev \
    liblapack-dev \
    libopenblas-dev \
    libtbb-dev \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

COPY . .

RUN pip install --no-cache-dir --break-system-packages cmake -r requirements.txt

# TNL's CUDA benchmarks require NVIDIA CCCL (Thrust/CUB); it ships with the CUDA
# toolkit but is not on cmake's default search path, so point find_package(CCCL) at it.
ENV CCCL_DIR=/usr/local/cuda-12.8/targets/x86_64-linux/lib/cmake/cccl

CMD ["python", "-m", "src.main"]