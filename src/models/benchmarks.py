from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class Benchmark(Base):
    __tablename__ = "benchmark"

    id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_name = Column(String(255), nullable=False, unique=True)

    operations = relationship("BenchmarkOperation", back_populates="benchmark")


class BenchmarkOperation(Base):
    __tablename__ = "benchmark_operation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_id = Column(Integer, ForeignKey("benchmark.id"), nullable=False)
    operation_name = Column(String(255), nullable=False)

    benchmark = relationship("Benchmark", back_populates="operations")
    results = relationship("BenchmarkResult", back_populates="operation")


class BenchmarkResult(Base):
    __tablename__ = "benchmark_result"
    __table_args__ = (
        Index("ix_benchmark_results_run_id", "run_id"),
        Index("ix_benchmark_results_operation_id", "operation_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_id = Column(Integer, ForeignKey("benchmark_operation.id"), nullable=False)
    run_id = Column(Integer, ForeignKey("benchmark_run.id"), nullable=False)
    time = Column(Float, nullable=False)
    time_median = Column(Float, nullable=True)
    stddev = Column(Float, nullable=False)
    stddev_time = Column(Float, nullable=False)
    loops = Column(Integer, nullable=False)
    bandwidth = Column(Float, nullable=True)
    cpu_cycles = Column(Float, nullable=True)
    cpu_cycles_median = Column(Float, nullable=True)
    cpu_cycles_stddev = Column(Float, nullable=True)
    cpu_cycles_per_operation = Column(Float, nullable=True)
    ops_per_loop = Column(Integer, nullable=True)

    operation = relationship("BenchmarkOperation", back_populates="results")
    run = relationship("BenchmarkRun", back_populates="results")
    metadata_entries = relationship(
        "BenchmarkResultMetadata", back_populates="result", cascade="all, delete-orphan"
    )


class BenchmarkResultMetadata(Base):
    __tablename__ = "benchmark_result_metadata"
    __table_args__ = (
        Index("ix_benchmark_result_metadata_result_id", "result_id"),
        UniqueConstraint(
            "result_id", "key", name="uq_benchmark_result_metadata_result_key"
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(Integer, ForeignKey("benchmark_result.id"), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(String(1024), nullable=True)

    result = relationship("BenchmarkResult", back_populates="metadata_entries")


class BenchmarkRun(Base):
    __tablename__ = "benchmark_run"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_hash = Column(String(128), nullable=False, unique=True)
    benchmark_id = Column(Integer, ForeignKey("benchmark.id"), nullable=False)
    machine_id = Column(Integer, ForeignKey("benchmark_machine.id"), nullable=False)
    start_time = Column(TIMESTAMP, nullable=False, default=func.now())
    end_time = Column(TIMESTAMP, nullable=False)
    duration = Column(Float, nullable=False)
    source_url = Column(String, nullable=False)
    source_version = Column(String(64), nullable=False)

    results = relationship("BenchmarkResult", back_populates="run")
    machine = relationship("BenchmarkMachine", back_populates="runs")


class BenchmarkMachine(Base):
    __tablename__ = "benchmark_machine"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_hash = Column(String(128), nullable=False, unique=True)
    cpu_cache_sizes = Column(String(255), nullable=True)
    cpu_cores = Column(Integer, nullable=False)
    cpu_max_frequency = Column(Integer, nullable=False)
    cpu_model_name = Column(String(255), nullable=True)
    cpu_threads_per_core = Column(Integer, nullable=False)
    gpu_cuda_cores = Column(Integer, nullable=True)
    gpu_architecture = Column(Float, nullable=True)
    gpu_clock_rate_mhz = Column(Float, nullable=True)
    gpu_global_memory_gb = Column(Float, nullable=True)
    gpu_memory_ecc_enabled = Column(Boolean, nullable=True)
    gpu_memory_clock_rate_mhz = Column(Float, nullable=True)
    gpu_name = Column(String(255), nullable=True)
    openmp_enabled = Column(Boolean, nullable=False)
    openmp_threads = Column(Integer, nullable=False)
    architecture = Column(String(255), nullable=True)
    host_name = Column(String(255), nullable=True)
    system = Column(String(255), nullable=True)
    system_release = Column(String(255), nullable=True)

    runs = relationship("BenchmarkRun", back_populates="machine")
