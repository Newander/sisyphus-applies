"""Add application tags.

Revision ID: 0006_application_tags
Revises: 0005_application_flow_values
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_application_tags"
down_revision: str | None = "0005_application_flow_values"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not table_exists("application_tags"):
        op.create_table(
            "application_tags",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("kind", sa.String(length=100), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("source", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
        op.create_index(op.f("ix_application_tags_kind"), "application_tags", ["kind"])
        op.create_index(op.f("ix_application_tags_name"), "application_tags", ["name"])

    if not table_exists("job_application_tags"):
        op.create_table(
            "job_application_tags",
            sa.Column("application_id", sa.Integer(), nullable=False),
            sa.Column("tag_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ["application_id"], ["job_applications.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["tag_id"], ["application_tags.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("application_id", "tag_id"),
        )


def downgrade() -> None:
    op.drop_table("job_application_tags", if_exists=True)
    op.drop_index(op.f("ix_application_tags_name"), table_name="application_tags", if_exists=True)
    op.drop_index(op.f("ix_application_tags_kind"), table_name="application_tags", if_exists=True)
    op.drop_table("application_tags", if_exists=True)
