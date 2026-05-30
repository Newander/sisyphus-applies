"""Add application seniority.

Revision ID: 0015_application_seniority
Revises: 0014_app_rejected_status
Create Date: 2026-05-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_application_seniority"
down_revision: str | None = "0014_app_rejected_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not column_exists("job_applications", "seniority"):
        op.add_column(
            "job_applications",
            sa.Column("seniority", sa.String(length=100), nullable=True),
        )


def downgrade() -> None:
    if column_exists("job_applications", "seniority"):
        op.drop_column("job_applications", "seniority")
