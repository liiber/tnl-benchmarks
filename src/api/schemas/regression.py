from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegressionBaselineUpsertRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    baseline_run_id: int = Field(alias="baselineRunId", ge=1)


class RegressionBaselineResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    benchmark: str
    baseline_run_id: int = Field(alias="baselineRunId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class RegressionCompareRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    baseline_run_id: int | None = Field(default=None, alias="baselineRunId", ge=1)
    target_run_id: int | None = Field(default=None, alias="targetRunId", ge=1)
    benchmarks: list[str] | None = None
    operations: list[str] | None = None
    performers: list[str] | None = None
    precisions: list[str] | None = None
    time_regression_threshold_pct: float = Field(
        default=5.0, alias="timeRegressionThresholdPct", ge=0
    )


class RegressionItemResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    benchmark: str
    operation: str
    metadata: dict[str, str | None]
    baseline_run_id: int = Field(alias="baselineRunId")
    target_run_id: int = Field(alias="targetRunId")
    baseline_time: float = Field(alias="baselineTime")
    target_time: float = Field(alias="targetTime")
    time_change_pct: float | None = Field(alias="timeChangePct")
    is_regression: bool = Field(alias="isRegression")
    is_improvement: bool = Field(alias="isImprovement")


class RegressionRunSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    benchmark: str
    baseline_run_id: int = Field(alias="baselineRunId")
    target_run_id: int = Field(alias="targetRunId")
    compared_items: int = Field(alias="comparedItems")
    regressions: int
    improvements: int
    missing_in_target: int = Field(alias="missingInTarget")
    new_in_target: int = Field(alias="newInTarget")
    missing_operations: list[str] = Field(alias="missingOperations")
    new_operations: list[str] = Field(alias="newOperations")


class RegressionCompareResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    has_regressions: bool = Field(alias="hasRegressions")
    summaries: list[RegressionRunSummary]
    items: list[RegressionItemResponse]
