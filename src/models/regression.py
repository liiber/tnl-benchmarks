from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base
from src.models.benchmarks import BenchmarkRun


class RegressionBaseline(Base):
    __tablename__ = "regression_baseline"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    benchmark_name: Mapped[str] = mapped_column(String(255), unique=True)
    baseline_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("benchmark_run.id")
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    baseline_run: Mapped[BenchmarkRun] = relationship()
