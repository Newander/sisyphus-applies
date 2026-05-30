"""Add application sources.

Revision ID: 0010_application_sources
Revises: 0009_app_status
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_application_sources"
down_revision: str | None = "0009_app_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not table_exists("application_sources"):
        op.create_table(
            "application_sources",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
        op.create_index(
            op.f("ix_application_sources_name"),
            "application_sources",
            ["name"],
            unique=False,
        )

    if not column_exists("job_applications", "application_source_id"):
        op.add_column(
            "job_applications",
            sa.Column("application_source_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_job_applications_application_source_id_application_sources",
            "job_applications",
            "application_sources",
            ["application_source_id"],
            ["id"],
        )


def downgrade() -> None:
    if column_exists("job_applications", "application_source_id"):
        op.drop_constraint(
            "fk_job_applications_application_source_id_application_sources",
            "job_applications",
            type_="foreignkey",
        )
        op.drop_column("job_applications", "application_source_id")

    if table_exists("application_sources"):
        op.drop_index(op.f("ix_application_sources_name"), table_name="application_sources")
        op.drop_table("application_sources")
