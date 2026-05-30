"""Add company notes.

Revision ID: 0002_company_notes
Revises: 0001_initial_schema
Create Date: 2026-05-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_company_notes"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not column_exists("companies", "notes"):
        op.add_column("companies", sa.Column("notes", sa.Text(), nullable=True))

    if not column_exists("companies", "updated_at"):
        op.add_column(
            "companies",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )


def downgrade() -> None:
    if column_exists("companies", "updated_at"):
        op.drop_column("companies", "updated_at")
    if column_exists("companies", "notes"):
        op.drop_column("companies", "notes")
