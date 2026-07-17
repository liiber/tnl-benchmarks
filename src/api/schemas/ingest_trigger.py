from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IngestTriggerRequest(BaseModel):
    skip_prepare: bool = Field(default=False, alias="skipPrepare")

    model_config = ConfigDict(populate_by_name=True)


class IngestTriggerResponse(BaseModel):
    status: str
    pid: int
    started_at: datetime = Field(alias="startedAt")
    log_path: str = Field(alias="logPath")

    model_config = ConfigDict(populate_by_name=True)


class IngestStatusResponse(BaseModel):
    status: str
    pid: int | None = None
    started_at: datetime | None = Field(default=None, alias="startedAt")
    finished_at: datetime | None = Field(default=None, alias="finishedAt")
    exit_code: int | None = Field(default=None, alias="exitCode")
    log_path: str = Field(alias="logPath")

    model_config = ConfigDict(populate_by_name=True)
