"""Add explicit application position URL.

Revision ID: 0011_application_position_url
Revises: 0010_application_sources
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_application_position_url"
down_revision: str | None = "0010_application_sources"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not column_exists("job_applications", "position_url"):
        op.add_column(
            "job_applications",
            sa.Column("position_url", sa.String(length=1000), nullable=True),
        )
        op.execute(
            "UPDATE job_applications SET position_url = source_url "
            "WHERE position_url IS NULL AND source_url IS NOT NULL"
        )


def downgrade() -> None:
    if column_exists("job_applications", "position_url"):
        op.drop_column("job_applications", "position_url")
