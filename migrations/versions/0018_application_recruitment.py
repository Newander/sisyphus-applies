"""add recruitment_description to job_applications

Revision ID: 0018_application_recruitment
Revises: 0016_application_contact
Create Date: 2026-05-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0018_application_recruitment"
down_revision = "0016_application_contact"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "job_applications", sa.Column("recruitment_description", sa.Text(), nullable=True)
    )


def downgrade():
    op.drop_column("job_applications", "recruitment_description")
