"""Normalize application flow values.

Revision ID: 0005_application_flow_values
Revises: 0004_cascade_application_updates
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_application_flow_values"
down_revision: str | None = "0004_cascade_application_updates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NEW_STATUS_VALUES = (
    "sent_cv",
    "recruiter_call",
    "receive_response",
    "interview_scheduled",
    "interview_finished",
    "offer",
)
OLD_STATUS_NAMES = (
    "DRAFT",
    "APPLIED",
    "INTERVIEWING",
    "OFFER",
    "REJECTED",
    "WITHDRAWN",
    "GHOSTED",
)


def table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def add_postgres_status_values(values: tuple[str, ...]) -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    with op.get_context().autocommit_block():
        for status in values:
            op.execute(f"ALTER TYPE application_status ADD VALUE IF NOT EXISTS '{status}'")


def normalize_application_statuses() -> None:
    status_map = {
        "DRAFT": "sent_cv",
        "draft": "sent_cv",
        "APPLIED": "sent_cv",
        "applied": "sent_cv",
        "SENT_CV": "sent_cv",
        "INTERVIEWING": "interview_scheduled",
        "interviewing": "interview_scheduled",
        "INTERVIEW_SCHEDULED": "interview_scheduled",
        "INTERVIEW_FINISHED": "interview_finished",
        "REJECTED": "receive_response",
        "rejected": "receive_response",
        "WITHDRAWN": "receive_response",
        "withdrawn": "receive_response",
        "GHOSTED": "receive_response",
        "ghosted": "receive_response",
        "RECEIVE_RESPONSE": "receive_response",
        "OFFER": "offer",
    }

    for old_value, new_value in status_map.items():
        op.execute(
            sa.text(
                """
                UPDATE job_applications
                SET status = CAST(:new_value AS application_status)
                WHERE status::text = :old_value
                """
            ).bindparams(new_value=new_value, old_value=old_value)
        )


def normalize_update_types() -> None:
    update_type_map = {
        "created": "sent_cv",
        "interview": "interview_scheduled",
        "status_changed": "receive_response",
    }

    for old_value, new_value in update_type_map.items():
        op.execute(
            sa.text(
                """
                UPDATE application_updates
                SET update_type = :new_value
                WHERE update_type = :old_value
                """
            ).bindparams(new_value=new_value, old_value=old_value)
        )


def upgrade() -> None:
    add_postgres_status_values(NEW_STATUS_VALUES)
    if table_exists("job_applications"):
        normalize_application_statuses()
    if table_exists("application_updates"):
        normalize_update_types()


def downgrade() -> None:
    add_postgres_status_values(OLD_STATUS_NAMES)

    if table_exists("job_applications"):
        op.execute(
            """
            UPDATE job_applications
            SET status = CAST('APPLIED' AS application_status)
            WHERE status::text = 'sent_cv'
            """
        )
        op.execute(
            """
            UPDATE job_applications
            SET status = CAST('INTERVIEWING' AS application_status)
            WHERE status::text IN ('interview_scheduled', 'interview_finished')
            """
        )
        op.execute(
            """
            UPDATE job_applications
            SET status = CAST('APPLIED' AS application_status)
            WHERE status::text = 'receive_response'
            """
        )
        op.execute(
            """
            UPDATE job_applications
            SET status = CAST('OFFER' AS application_status)
            WHERE status::text = 'offer'
            """
        )

    if table_exists("application_updates"):
        op.execute(
            "UPDATE application_updates SET update_type = 'created' WHERE update_type = 'sent_cv'"
        )
        op.execute(
            """
            UPDATE application_updates
            SET update_type = 'interview'
            WHERE update_type IN ('interview_scheduled', 'interview_finished')
            """
        )
        op.execute(
            """
            UPDATE application_updates
            SET update_type = 'status_changed'
            WHERE update_type IN ('receive_response', 'offer')
            """
        )
