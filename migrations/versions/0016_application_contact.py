"""add contact fields to job_applications

Revision ID: 0016_application_contact
Revises: 0015_application_seniority
Create Date: 2026-05-28

"""
from alembic import op
import sqlalchemy as sa

revision = '0016_application_contact'
down_revision = '0015_application_seniority'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('job_applications', sa.Column('contact_url', sa.String(1000), nullable=True))
    op.add_column('job_applications', sa.Column('contact_description', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('job_applications', 'contact_description')
    op.drop_column('job_applications', 'contact_url')
