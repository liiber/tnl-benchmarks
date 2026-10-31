from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base


class Benchmark(Base):
    __tablename__ = "benchmark"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    benchmark_name: Mapped[str] = mapped_column(String(255), unique=True)

    operations: Mapped[list[BenchmarkOperation]] = relationship(
        back_populates="benchmark"
    )


class BenchmarkOperation(Base):
    __tablename__ = "benchmark_operation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    benchmark_id: Mapped[int] = mapped_column(Integer, ForeignKey("benchmark.id"))
    operation_name: Mapped[str] = mapped_column(String(255))

    benchmark: Mapped[Benchmark] = relationship(back_populates="operations")
    results: Mapped[list[BenchmarkResult]] = relationship(back_populates="operation")


class BenchmarkResult(Base):
    __tablename__ = "benchmark_result"
    __table_args__ = (
        Index("ix_benchmark_results_run_id", "run_id"),
        Index("ix_benchmark_results_operation_id", "operation_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("benchmark_operation.id")
    )
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("benchmark_run.id"))
    time: Mapped[float] = mapped_column(Float)
    time_median: Mapped[float | None] = mapped_column(Float)
    stddev: Mapped[float] = mapped_column(Float)
    stddev_time: Mapped[float] = mapped_column(Float)
    loops: Mapped[int] = mapped_column(Integer)
    bandwidth: Mapped[float | None] = mapped_column(Float)
    cpu_cycles: Mapped[float | None] = mapped_column(Float)
    cpu_cycles_median: Mapped[float | None] = mapped_column(Float)
    cpu_cycles_stddev: Mapped[float | None] = mapped_column(Float)
    cpu_cycles_per_operation: Mapped[float | None] = mapped_column(Float)
    ops_per_loop: Mapped[int | None] = mapped_column(Integer)

    operation: Mapped[BenchmarkOperation] = relationship(back_populates="results")
    run: Mapped[BenchmarkRun] = relationship(back_populates="results")
    metadata_entries: Mapped[list[BenchmarkResultMetadata]] = relationship(
        back_populates="result", cascade="all, delete-orphan"
    )


class BenchmarkResultMetadata(Base):
    __tablename__ = "benchmark_result_metadata"
    __table_args__ = (
        Index("ix_benchmark_result_metadata_result_id", "result_id"),
        UniqueConstraint(
            "result_id", "key", name="uq_benchmark_result_metadata_result_key"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    result_id: Mapped[int] = mapped_column(Integer, ForeignKey("benchmark_result.id"))
    key: Mapped[str] = mapped_column(String(255))
    value: Mapped[str | None] = mapped_column(String(1024))

    result: Mapped[BenchmarkResult] = relationship(back_populates="metadata_entries")


class BenchmarkRun(Base):
    __tablename__ = "benchmark_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_hash: Mapped[str] = mapped_column(String(128), unique=True)
    benchmark_id: Mapped[int] = mapped_column(Integer, ForeignKey("benchmark.id"))
    machine_id: Mapped[int] = mapped_column(Integer, ForeignKey("benchmark_machine.id"))
    start_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    end_time: Mapped[datetime] = mapped_column(TIMESTAMP)
    duration: Mapped[float] = mapped_column(Float)
    source_url: Mapped[str] = mapped_column(String)
    source_version: Mapped[str] = mapped_column(String(64))

    results: Mapped[list[BenchmarkResult]] = relationship(back_populates="run")
    machine: Mapped[BenchmarkMachine] = relationship(back_populates="runs")


class BenchmarkMachine(Base):
    __tablename__ = "benchmark_machine"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_hash: Mapped[str] = mapped_column(String(128), unique=True)
    cpu_cache_sizes: Mapped[str | None] = mapped_column(String(255))
    cpu_cores: Mapped[int] = mapped_column(Integer)
    cpu_max_frequency: Mapped[int] = mapped_column(Integer)
    cpu_model_name: Mapped[str | None] = mapped_column(String(255))
    cpu_threads_per_core: Mapped[int] = mapped_column(Integer)
    gpu_cuda_cores: Mapped[int | None] = mapped_column(Integer)
    gpu_architecture: Mapped[float | None] = mapped_column(Float)
    gpu_clock_rate_mhz: Mapped[float | None] = mapped_column(Float)
    gpu_global_memory_gb: Mapped[float | None] = mapped_column(Float)
    gpu_memory_ecc_enabled: Mapped[bool | None] = mapped_column(Boolean)
    gpu_memory_clock_rate_mhz: Mapped[float | None] = mapped_column(Float)
    gpu_name: Mapped[str | None] = mapped_column(String(255))
    openmp_enabled: Mapped[bool] = mapped_column(Boolean)
    openmp_threads: Mapped[int] = mapped_column(Integer)
    architecture: Mapped[str | None] = mapped_column(String(255))
    host_name: Mapped[str | None] = mapped_column(String(255))
    system: Mapped[str | None] = mapped_column(String(255))
    system_release: Mapped[str | None] = mapped_column(String(255))

    runs: Mapped[list[BenchmarkRun]] = relationship(back_populates="machine")
