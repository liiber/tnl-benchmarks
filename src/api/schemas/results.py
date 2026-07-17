from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkResultResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    benchmark: str
    operation: str
    run_id: int = Field(alias="runId")
    run_hash: str = Field(alias="runHash")
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    duration: float
    source_version: str = Field(alias="sourceVersion")
    machine: str | None
    time: float
    time_median: float | None = Field(alias="timeMedian")
    stddev: float
    stddev_time: float = Field(alias="stddevTime")
    loops: int
    bandwidth: float | None
    cpu_cycles: float | None = Field(alias="cpuCycles")
    cpu_cycles_median: float | None = Field(alias="cpuCyclesMedian")
    cpu_cycles_stddev: float | None = Field(alias="cpuCyclesStddev")
    cpu_cycles_per_operation: float | None = Field(alias="cpuCyclesPerOperation")
    ops_per_loop: int | None = Field(alias="opsPerLoop")
    metadata: dict[str, str | None]


class BenchmarkResultsFilterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date_from: datetime | None = Field(default=None, alias="dateFrom")
    date_to: datetime | None = Field(default=None, alias="dateTo")
    benchmarks: list[str] | None = None
    operations: list[str] | None = None
    performers: list[str] | None = None
    precisions: list[str] | None = None
    limit: int = Field(default=200, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class BenchmarkResultsPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[BenchmarkResultResponse]
