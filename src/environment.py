from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CMakeBuildType = Literal["Release", "Debug", "RelWithDebInfo", "MinSizeRel"]


class Environment(BaseSettings):
    APP_PORT: int = 8000

    @field_validator("TNL_BENCHMARK_TIMEOUT_SECONDS", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v

    DB_USER: str = Field(..., min_length=3)
    DB_PASSWORD: str = Field(..., min_length=3)
    DB_NAME: str = Field(..., min_length=3)
    DB_HOST: str = Field(..., min_length=3)
    DB_PORT: int = 5432
    TNL_REPO_URL: str = Field(...)
    WORKSPACE_PATH: str = "/workspace"
    INGEST_TRIGGER_TOKEN: str | None = None
    TNL_CMAKE_BUILD_TYPE: CMakeBuildType = "Release"
    TNL_USE_CUDA: bool = False
    TNL_USE_HIP: bool = False
    TNL_USE_OPENMP: bool = True
    TNL_USE_MPI: bool = False
    TNL_BUILD_TARGET: str = "benchmarks"
    TNL_BENCHMARK_NAMING_PATTERN: str = "tnl-benchmark"
    TNL_BENCHMARK_TIMEOUT_SECONDS: int | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


ENV = Environment()
