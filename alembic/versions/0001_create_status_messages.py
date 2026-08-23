"""create node status messages

Revision ID: 0001_create_status_messages
Revises:
Create Date: 2026-07-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "0001_create_status_messages"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if "node_status_messages" in inspect(op.get_bind()).get_table_names():
        return

    op.create_table(
        "node_status_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("node_id", sa.String(length=100), nullable=False),
        sa.Column("pid", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_reason", sa.String(length=16), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_node_status_messages_node_id", "node_status_messages", ["node_id"])
    op.create_index("ix_node_status_messages_expires_at", "node_status_messages", ["expires_at"])
    op.create_index(
        "uq_active_status_message_per_node",
        "node_status_messages",
        ["node_id"],
        unique=True,
        sqlite_where=sa.text("ended_at IS NULL"),
        postgresql_where=sa.text("ended_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_active_status_message_per_node", table_name="node_status_messages")
    op.drop_index("ix_node_status_messages_expires_at", table_name="node_status_messages")
    op.drop_index("ix_node_status_messages_node_id", table_name="node_status_messages")
    op.drop_table("node_status_messages")
