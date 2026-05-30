"""add cover_letter to job_applications

Revision ID: 0019_application_cover_letter
Revises: 0018_application_recruitment, 0017_prompts
Create Date: 2026-05-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0019_application_cover_letter"
down_revision = ("0018_application_recruitment", "0017_prompts")
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("job_applications", sa.Column("cover_letter", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("job_applications", "cover_letter")
