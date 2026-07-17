"""Mapping of raw benchmark metadata onto database model fields."""

from src.ingest.formatting import (
    normalize_nullable,
    to_optional_bool_from_int,
    to_optional_float,
    to_optional_int,
)


def build_machine_fields(metadata: dict) -> dict:
    """Map a parsed ``.metadata.json`` dict onto ``BenchmarkMachine`` column values.

    Hardware/system attributes are stored by TNL under human-readable keys (e.g.
    ``"CPU model name"``). This normalizes them into the column names and types used
    by the ORM model, applying the same conversions as the rest of the ingest pipeline.
    """
    return {
        "cpu_cache_sizes": metadata.get("CPU cache sizes (L1d, L1i, L2, L3) (kiB)")
        or None,
        "cpu_cores": to_optional_int(metadata.get("CPU cores")) or 0,
        "cpu_max_frequency": to_optional_int(metadata.get("CPU max frequency (MHz)"))
        or 0,
        "cpu_model_name": normalize_nullable(metadata.get("CPU model name")),
        "cpu_threads_per_core": to_optional_int(metadata.get("CPU threads per core"))
        or 0,
        "gpu_name": normalize_nullable(metadata.get("GPU name")),
        "gpu_cuda_cores": to_optional_int(metadata.get("GPU CUDA cores")),
        "gpu_architecture": to_optional_float(metadata.get("GPU architecture")),
        "gpu_clock_rate_mhz": to_optional_float(metadata.get("GPU clock rate (MHz)")),
        "gpu_global_memory_gb": to_optional_float(
            metadata.get("GPU global memory (GB)")
        ),
        "gpu_memory_ecc_enabled": to_optional_bool_from_int(
            metadata.get("GPU memory ECC enabled")
        ),
        "gpu_memory_clock_rate_mhz": to_optional_float(
            metadata.get("GPU memory clock rate (MHz)")
        ),
        "openmp_enabled": metadata.get("OpenMP enabled", "no") == "yes",
        "openmp_threads": to_optional_int(metadata.get("OpenMP threads")) or 0,
        "architecture": normalize_nullable(metadata.get("architecture")),
        "host_name": normalize_nullable(metadata.get("host name")),
        "system": normalize_nullable(metadata.get("system")),
        "system_release": normalize_nullable(metadata.get("system release")),
    }
