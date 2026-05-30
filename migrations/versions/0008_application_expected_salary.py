"""Add expected salary range.

Revision ID: 0008_application_expected_salary
Revises: 0007_application_raw_position
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_application_expected_salary"
down_revision: str | None = "0007_application_raw_position"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not column_exists("job_applications", "expected_salary_min_pln"):
        op.add_column(
            "job_applications",
            sa.Column("expected_salary_min_pln", sa.Integer(), nullable=True),
        )
    if not column_exists("job_applications", "expected_salary_max_pln"):
        op.add_column(
            "job_applications",
            sa.Column("expected_salary_max_pln", sa.Integer(), nullable=True),
        )


def downgrade() -> None:
    if column_exists("job_applications", "expected_salary_max_pln"):
        op.drop_column("job_applications", "expected_salary_max_pln")
    if column_exists("job_applications", "expected_salary_min_pln"):
        op.drop_column("job_applications", "expected_salary_min_pln")
