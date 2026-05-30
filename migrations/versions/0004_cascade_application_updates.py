"""Cascade application updates when deleting job applications.

Revision ID: 0004_cascade_application_updates
Revises: 0003_gmail_integration
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_cascade_application_updates"
down_revision: str | None = "0003_gmail_integration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


CASCADE_FK_NAME = "fk_application_updates_application_id_job_applications"


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _application_updates_fk_name() -> str | None:
    inspector = sa.inspect(op.get_bind())
    for foreign_key in inspector.get_foreign_keys("application_updates"):
        if (
            foreign_key["constrained_columns"] == ["application_id"]
            and foreign_key["referred_table"] == "job_applications"
        ):
            return foreign_key["name"]
    return None


def _replace_application_updates_fk(*, ondelete: str | None) -> None:
    if not _table_exists("application_updates") or not _table_exists("job_applications"):
        return

    existing_name = _application_updates_fk_name()
    if existing_name:
        op.drop_constraint(existing_name, "application_updates", type_="foreignkey")

    op.create_foreign_key(
        CASCADE_FK_NAME,
        "application_updates",
        "job_applications",
        ["application_id"],
        ["id"],
        ondelete=ondelete,
    )


def upgrade() -> None:
    _replace_application_updates_fk(ondelete="CASCADE")


def downgrade() -> None:
    _replace_application_updates_fk(ondelete=None)
