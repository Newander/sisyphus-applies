"""Add feature memories.

Revision ID: 0012_feature_memories
Revises: 0011_application_position_url
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_feature_memories"
down_revision: str | None = "0011_application_position_url"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if table_exists("feature_memories"):
        return

    op.create_table(
        "feature_memories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_url", sa.String(length=2000), nullable=False),
        sa.Column("page_title", sa.String(length=500), nullable=True),
        sa.Column("screenshot_data_url", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_feature_memories_closed_at",
        "feature_memories",
        ["closed_at"],
        unique=False,
    )


def downgrade() -> None:
    if table_exists("feature_memories"):
        op.drop_index("ix_feature_memories_closed_at", table_name="feature_memories")
        op.drop_table("feature_memories")
