"""Add raw position snapshots.

Revision ID: 0007_application_raw_position
Revises: 0006_application_tags
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_application_raw_position"
down_revision: str | None = "0006_application_tags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not column_exists("job_applications", "raw_position_text"):
        op.add_column("job_applications", sa.Column("raw_position_text", sa.Text(), nullable=True))
    if not column_exists("job_applications", "raw_position_source"):
        op.add_column(
            "job_applications",
            sa.Column("raw_position_source", sa.String(length=50), nullable=True),
        )


def downgrade() -> None:
    if column_exists("job_applications", "raw_position_source"):
        op.drop_column("job_applications", "raw_position_source")
    if column_exists("job_applications", "raw_position_text"):
        op.drop_column("job_applications", "raw_position_text")
