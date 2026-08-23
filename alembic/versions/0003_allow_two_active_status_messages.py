"""allow two active status messages per node

Revision ID: 0003_allow_two_active_status_messages
Revises: 0002_create_reports
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "0003_allow_two_active_status_messages"
down_revision: Union[str, Sequence[str], None] = "0002_create_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    index_names = {index["name"] for index in inspect(op.get_bind()).get_indexes("node_status_messages")}
    if "uq_active_status_message_per_node" in index_names:
        op.drop_index("uq_active_status_message_per_node", table_name="node_status_messages")


def downgrade() -> None:
    op.create_index(
        "uq_active_status_message_per_node",
        "node_status_messages",
        ["node_id"],
        unique=True,
        sqlite_where=sa.text("ended_at IS NULL"),
        postgresql_where=sa.text("ended_at IS NULL"),
    )
