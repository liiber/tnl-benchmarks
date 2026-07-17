from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class RegressionBaseline(Base):
    __tablename__ = "regression_baseline"

    id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_name = Column(String(255), nullable=False, unique=True)
    baseline_run_id = Column(Integer, ForeignKey("benchmark_run.id"), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    baseline_run = relationship("BenchmarkRun")
