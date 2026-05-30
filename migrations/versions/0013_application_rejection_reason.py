"""Add application rejection reason.

Revision ID: 0013_app_rejection_reason
Revises: 0012_feature_memories
Create Date: 2026-05-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_app_rejection_reason"
down_revision: str | None = "0012_feature_memories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not column_exists("job_applications", "rejection_reason"):
        op.add_column(
            "job_applications",
            sa.Column("rejection_reason", sa.String(length=500), nullable=True),
        )


def downgrade() -> None:
    if column_exists("job_applications", "rejection_reason"):
        op.drop_column("job_applications", "rejection_reason")
