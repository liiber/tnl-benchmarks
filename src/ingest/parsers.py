import json
from collections.abc import Mapping
from typing import TypedDict

from src.ingest.formatting import (
    AnyValue,
    convert_to_optional_float,
    convert_to_optional_int,
    normalize_nullable,
)

_METRIC_SOURCE_KEYS = frozenset(
    {
        "time",
        "time_median",
        "time_stddev",
        "stddev",
        "time_stddev/time",
        "stddev/time",
        "loops",
        "bandwidth",
        "cycles",
        "cycles_median",
        "cycles_stddev",
        "cycles/op",
        "cycles_stddev/cycles",
        "ops_per_loop",
        # "speedup" is a derived, run-varying ratio (the speedup column was dropped from
        # the schema). Excluded here so it is not stored as metadata, where it would
        # otherwise become part of the regression composite key and break run matching.
        "speedup",
    }
)

# TNL names the operation field differently across benchmark families: most use
# "operation", the segments benchmark uses "function", and the sort benchmark only
# carries the algorithm name in "performer". We take the first present of these.
_OPERATION_KEYS = ("operation", "function", "performer")


class ParsedMetrics(TypedDict):
    time: float
    time_median: float | None
    stddev: float
    stddev_time: float
    loops: int
    bandwidth: float | None
    cpu_cycles: float | None
    cpu_cycles_median: float | None
    cpu_cycles_stddev: float | None
    cpu_cycles_per_operation: float | None
    ops_per_loop: int | None


class ParsedRow(TypedDict):
    operation: str | None
    metrics: ParsedMetrics
    metadata: dict[str, str | None]


def _resolve_operation(row: Mapping[str, AnyValue]) -> tuple[str | None, str | None]:
    """Return ``(operation_value, source_key)`` for a parsed log row.

    ``source_key`` is the key the operation was taken from (or ``None`` if the row
    has no recognizable operation field) so the caller can exclude it from metadata.
    """
    for key in _OPERATION_KEYS:
        value = normalize_nullable(row.get(key))
        if value:
            return str(value), key
    return None, None


def parse_metadata(path: str) -> dict[str, AnyValue]:
    with open(path) as file:
        metadata = json.load(file)
    if not isinstance(metadata, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return metadata


def parse_log(path: str) -> list[ParsedRow]:
    results: list[ParsedRow] = []

    with open(path) as file:
        for line in file:
            line = line.strip()

            if not line.startswith("{"):
                continue

            row = json.loads(line)

            metrics: ParsedMetrics = {
                "time": convert_to_optional_float(row.get("time")) or 0.0,
                "time_median": convert_to_optional_float(row.get("time_median")),
                "stddev": convert_to_optional_float(
                    row.get("time_stddev", row.get("stddev"))
                )
                or 0.0,
                "stddev_time": convert_to_optional_float(
                    row.get("time_stddev/time", row.get("stddev/time"))
                )
                or 0.0,
                "loops": convert_to_optional_int(row.get("loops")) or 0,
                "bandwidth": convert_to_optional_float(row.get("bandwidth")),
                "cpu_cycles": convert_to_optional_float(row.get("cycles")),
                "cpu_cycles_median": convert_to_optional_float(
                    row.get("cycles_median")
                ),
                "cpu_cycles_stddev": convert_to_optional_float(
                    row.get("cycles_stddev")
                ),
                "cpu_cycles_per_operation": convert_to_optional_float(
                    row.get("cycles/op")
                ),
                "ops_per_loop": convert_to_optional_int(row.get("ops_per_loop")),
            }

            operation, operation_key = _resolve_operation(row)

            metadata = {
                k: str(v) if v is not None else None
                for k, v in row.items()
                if k != operation_key and k not in _METRIC_SOURCE_KEYS
            }

            results.append(
                {
                    "operation": operation,
                    "metrics": metrics,
                    "metadata": metadata,
                }
            )

    return results
