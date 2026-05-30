"""add prompts table

Revision ID: 0017_prompts
Revises: 0018_application_recruitment
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from alembic import op

revision = "0017_prompts"
down_revision = "0015_application_seniority"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prompts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_prompts_name", "prompts", ["name"])


def downgrade():
    op.drop_table("prompts")
