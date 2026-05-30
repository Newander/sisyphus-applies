"""Add Gmail integration tables.

Revision ID: 0003_gmail_integration
Revises: 0002_company_notes
Create Date: 2026-05-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_gmail_integration"
down_revision: str | None = "0002_company_notes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not table_exists("gmail_accounts"):
        op.create_table(
            "gmail_accounts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email_address", sa.String(length=320), nullable=False),
            sa.Column("history_id", sa.String(length=100), nullable=True),
            sa.Column(
                "connected_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
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
            sa.UniqueConstraint("email_address"),
        )
        op.create_index(
            op.f("ix_gmail_accounts_email_address"),
            "gmail_accounts",
            ["email_address"],
            unique=False,
        )
        op.create_index(
            op.f("ix_gmail_accounts_last_sync_at"),
            "gmail_accounts",
            ["last_sync_at"],
            unique=False,
        )

    if not table_exists("gmail_messages"):
        op.create_table(
            "gmail_messages",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("account_id", sa.Integer(), nullable=False),
            sa.Column("gmail_id", sa.String(length=255), nullable=False),
            sa.Column("thread_id", sa.String(length=255), nullable=False),
            sa.Column("history_id", sa.String(length=100), nullable=True),
            sa.Column("sender", sa.String(length=1000), nullable=True),
            sa.Column("recipients", sa.Text(), nullable=True),
            sa.Column("subject", sa.String(length=1000), nullable=True),
            sa.Column("snippet", sa.Text(), nullable=True),
            sa.Column("body_text", sa.Text(), nullable=True),
            sa.Column("label_ids", sa.JSON(), nullable=True),
            sa.Column("internal_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("raw_payload", sa.JSON(), nullable=True),
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
            sa.ForeignKeyConstraint(["account_id"], ["gmail_accounts.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("gmail_id"),
        )
        op.create_index(
            op.f("ix_gmail_messages_account_id"),
            "gmail_messages",
            ["account_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_gmail_messages_gmail_id"),
            "gmail_messages",
            ["gmail_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_gmail_messages_thread_id"),
            "gmail_messages",
            ["thread_id"],
            unique=False,
        )
        op.create_index(op.f("ix_gmail_messages_sender"), "gmail_messages", ["sender"])
        op.create_index(op.f("ix_gmail_messages_subject"), "gmail_messages", ["subject"])
        op.create_index(
            op.f("ix_gmail_messages_internal_date"),
            "gmail_messages",
            ["internal_date"],
        )
        op.create_index(
            op.f("ix_gmail_messages_received_at"),
            "gmail_messages",
            ["received_at"],
        )


def downgrade() -> None:
    op.drop_table("gmail_messages", if_exists=True)
    op.drop_table("gmail_accounts", if_exists=True)
