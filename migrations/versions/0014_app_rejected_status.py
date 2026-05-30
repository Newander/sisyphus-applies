"""Add rejected application status.

Revision ID: 0014_app_rejected_status
Revises: 0013_app_rejection_reason
Create Date: 2026-05-26
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0014_app_rejected_status"
down_revision: str | None = "0013_app_rejection_reason"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'rejected'")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(
        """
        UPDATE job_applications
        SET status = CAST('receive_response' AS application_status)
        WHERE status::text = 'rejected'
        """
    )
