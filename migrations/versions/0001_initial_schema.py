"""Initial schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


APPLICATION_STATUSES = (
    "sent_cv",
    "recruiter_call",
    "receive_response",
    "interview_scheduled",
    "interview_finished",
    "offer",
)
DOCUMENT_TYPES = ("CV", "COVER_LETTER", "PORTFOLIO", "OTHER")


def table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    application_status = postgresql.ENUM(
        *APPLICATION_STATUSES, name="application_status", create_type=False
    )
    document_type = postgresql.ENUM(*DOCUMENT_TYPES, name="document_type", create_type=False)
    application_status.create(bind, checkfirst=True)
    document_type.create(bind, checkfirst=True)

    if not table_exists("companies"):
        op.create_table(
            "companies",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("website", sa.String(length=500), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
        op.create_index(op.f("ix_companies_name"), "companies", ["name"], unique=False)

    if not table_exists("documents"):
        op.create_table(
            "documents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("file_name", sa.String(length=500), nullable=False),
            sa.Column("display_name", sa.String(length=500), nullable=False),
            sa.Column("path", sa.String(length=1000), nullable=False),
            sa.Column("document_type", document_type, nullable=False),
            sa.Column("mime_type", sa.String(length=255), nullable=True),
            sa.Column("size_bytes", sa.BigInteger(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("path"),
        )
        op.create_index(op.f("ix_documents_file_name"), "documents", ["file_name"], unique=False)

    if not table_exists("job_applications"):
        op.create_table(
            "job_applications",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("company_id", sa.Integer(), nullable=False),
            sa.Column("primary_document_id", sa.Integer(), nullable=True),
            sa.Column("position_title", sa.String(length=500), nullable=False),
            sa.Column("status", application_status, nullable=False),
            sa.Column("source_url", sa.String(length=1000), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_update_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
            sa.ForeignKeyConstraint(["primary_document_id"], ["documents.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_job_applications_applied_at"),
            "job_applications",
            ["applied_at"],
            unique=False,
        )
        op.create_index(
            op.f("ix_job_applications_company_id"),
            "job_applications",
            ["company_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_job_applications_last_update_at"),
            "job_applications",
            ["last_update_at"],
            unique=False,
        )
        op.create_index(
            op.f("ix_job_applications_position_title"),
            "job_applications",
            ["position_title"],
            unique=False,
        )
        op.create_index(
            op.f("ix_job_applications_status"),
            "job_applications",
            ["status"],
            unique=False,
        )

    if not table_exists("application_updates"):
        op.create_table(
            "application_updates",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("application_id", sa.Integer(), nullable=False),
            sa.Column("update_type", sa.String(length=100), nullable=False),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["application_id"], ["job_applications.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_application_updates_application_id"),
            "application_updates",
            ["application_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_application_updates_occurred_at"),
            "application_updates",
            ["occurred_at"],
            unique=False,
        )
        op.create_index(
            op.f("ix_application_updates_update_type"),
            "application_updates",
            ["update_type"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_table("application_updates", if_exists=True)
    op.drop_table("job_applications", if_exists=True)
    op.drop_table("documents", if_exists=True)
    op.drop_table("companies", if_exists=True)
    postgresql.ENUM(name="application_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="document_type").drop(bind, checkfirst=True)
