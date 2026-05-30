"""Add recruiter call application status.

Revision ID: 0009_app_status
Revises: 0008_application_expected_salary
Create Date: 2026-05-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009_app_status"
down_revision: str | None = "0008_application_expected_salary"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'recruiter_call'")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(
        """
        UPDATE job_applications
        SET status = CAST('sent_cv' AS application_status)
        WHERE status::text = 'recruiter_call'
        """
    )
