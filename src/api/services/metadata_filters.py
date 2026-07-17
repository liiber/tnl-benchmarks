"""Shared query helpers for filtering benchmark results by metadata."""

from collections.abc import Iterable

from sqlalchemy import Select, select

from src.models.benchmarks import BenchmarkResultMetadata


def metadata_value_filter(key: str, values: Iterable[str]) -> Select:
    """Subquery selecting ``benchmark_result`` ids whose metadata entry for ``key``
    has a value in ``values``.

    Metadata is stored in the EAV ``benchmark_result_metadata`` table, so dimension
    filters such as ``performer`` or ``precision`` are expressed as a subquery over
    that table rather than a column predicate. Intended for use as
    ``BenchmarkResult.id.in_(metadata_value_filter(...))``.
    """
    return (
        select(BenchmarkResultMetadata.result_id)
        .where(BenchmarkResultMetadata.key == key)
        .where(BenchmarkResultMetadata.value.in_(values))
    )
