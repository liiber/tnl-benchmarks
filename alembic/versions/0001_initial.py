"""Initial schema — creates all tables if they are missing

Revision ID: 0001
Revises:
Create Date: 2026-06-16

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names(schema="public"))

    from src.database import Base
    from src.models import benchmarks, regression  # noqa: F401

    # Create each missing table individually so we never hit the SQLAlchemy
    # checkfirst=True bug: create_all(checkfirst=True) emits CREATE TABLE IF NOT EXISTS
    # but still runs CREATE INDEX unconditionally, causing DuplicateTableError when
    # the table already exists.
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            table.create(conn)

    # Ensure indexes exist regardless of how the tables got there.
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_benchmark_results_run_id"
            " ON benchmark_result (run_id)"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_benchmark_results_operation_id"
            " ON benchmark_result (operation_id)"
        )
    )


def downgrade() -> None:
    pass
