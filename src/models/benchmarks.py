from sqlalchemy.orm import relationship
from src.database import Base
from sqlalchemy import Column, Integer, Enum, ForeignKey, Float, Boolean, TIMESTAMP, String
import enum
from sqlalchemy.sql import func


class Benchmark(Base):
    __tablename__ = "benchmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_name = Column(String(255), nullable=False, unique=True)

    operations = relationship("BenchmarkOperation", back_populates="benchmark")

class BenchmarkOperation(Base):
    __tablename__ = "benchmark_operations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_id = Column(Integer, ForeignKey("benchmarks.id"), nullable=False)
    operation_name = Column(String(255), nullable=False)

    benchmark = relationship("Benchmark", back_populates="operations")
    results = relationship("BenchmarkResult", back_populates="operation")

class ResultPrecision(str, enum.Enum):
    double = "double"
    float = "float"
    int = "int"

class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_id = Column(Integer,ForeignKey("benchmark_operations.id"), nullable=False)
    run_id = Column(Integer, ForeignKey("benchmark_runs.id"), nullable=False)
    precision = Column(Enum(ResultPrecision), server_default="double", nullable=False)
    host_allocator = Column(String(255), nullable=True)
    size = Column(Float, nullable=True)
    rows = Column(Integer, nullable=True)
    columns = Column(Integer, nullable=True)
    performer = Column(String(255), nullable=True)
    time = Column(Float, nullable=False)
    stddev = Column(Float, nullable=False)
    stddev_time = Column(Float, nullable=False)
    loops = Column(Integer, nullable=False)
    bandwidth = Column(Float, nullable=True)
    speedup = Column(Float, nullable=True)

    operation = relationship("BenchmarkOperation", back_populates="results")
    run = relationship("BenchmarkRun", back_populates="results")

class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_hash = Column(String(128), nullable=False, unique=True)
    benchmark_id = Column(Integer, ForeignKey("benchmarks.id"), nullable=False)
    machine_id = Column(Integer, ForeignKey("benchmark_machines.id"), nullable=False)
    start_time = Column(TIMESTAMP, nullable=False, default=func.now())
    end_time = Column(TIMESTAMP, nullable=False)
    duration = Column(Float, nullable=False)
    source_url = Column(String, nullable=False)
    source_version = Column(String(64), nullable=False) # Short Commit Hash of run benchmark
    source_checksum = Column(String(128), nullable=False)

    results = relationship("BenchmarkResult", back_populates="run")
    machine = relationship("BenchmarkMachine", back_populates="runs")

class BenchmarkMachine(Base):
    __tablename__ = "benchmark_machines"

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