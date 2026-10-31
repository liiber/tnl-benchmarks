"""Mapping of raw benchmark metadata onto database model fields."""

from collections.abc import Mapping

from src.ingest.formatting import (
    AnyValue,
    convert_int_to_optional_bool,
    convert_to_optional_float,
    convert_to_optional_int,
    normalize_nullable,
)


def build_machine_fields(metadata: Mapping[str, AnyValue]) -> dict[str, AnyValue]:
    """Map a parsed ``.metadata.json`` dict onto ``BenchmarkMachine`` column values.

    Hardware/system attributes are stored by TNL under human-readable keys (e.g.
    ``"CPU model name"``). This normalizes them into the column names and types used
    by the ORM model, applying the same conversions as the rest of the ingest pipeline.
    """
    return {
        "cpu_cache_sizes": metadata.get("CPU cache sizes (L1d, L1i, L2, L3) (kiB)")
        or None,
        "cpu_cores": convert_to_optional_int(metadata.get("CPU cores")) or 0,
        "cpu_max_frequency": convert_to_optional_int(
            metadata.get("CPU max frequency (MHz)")
        )
        or 0,
        "cpu_model_name": normalize_nullable(metadata.get("CPU model name")),
        "cpu_threads_per_core": convert_to_optional_int(
            metadata.get("CPU threads per core")
        )
        or 0,
        "gpu_name": normalize_nullable(metadata.get("GPU name")),
        "gpu_cuda_cores": convert_to_optional_int(metadata.get("GPU CUDA cores")),
        "gpu_architecture": convert_to_optional_float(metadata.get("GPU architecture")),
        "gpu_clock_rate_mhz": convert_to_optional_float(
            metadata.get("GPU clock rate (MHz)")
        ),
        "gpu_global_memory_gb": convert_to_optional_float(
            metadata.get("GPU global memory (GB)")
        ),
        "gpu_memory_ecc_enabled": convert_int_to_optional_bool(
            metadata.get("GPU memory ECC enabled")
        ),
        "gpu_memory_clock_rate_mhz": convert_to_optional_float(
            metadata.get("GPU memory clock rate (MHz)")
        ),
        "openmp_enabled": metadata.get("OpenMP enabled", "no") == "yes",
        "openmp_threads": convert_to_optional_int(metadata.get("OpenMP threads")) or 0,
        "architecture": normalize_nullable(metadata.get("architecture")),
        "host_name": normalize_nullable(metadata.get("host name")),
        "system": normalize_nullable(metadata.get("system")),
        "system_release": normalize_nullable(metadata.get("system release")),
    }
