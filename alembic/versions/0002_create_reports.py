"""create reports and report photos

Revision ID: 0002_create_reports
Revises: 0001_create_status_messages
Create Date: 2026-07-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "0002_create_reports"
down_revision: Union[str, Sequence[str], None] = "0001_create_status_messages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    table_names = inspect(op.get_bind()).get_table_names()
    if "reports" not in table_names:
        op.create_table(
            "reports",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("node_id", sa.String(length=100), nullable=False),
            sa.Column("pid", sa.String(length=100), nullable=False),
            sa.Column("category", sa.String(length=32), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("lat", sa.Float(), nullable=False),
            sa.Column("lon", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_reports_node_id", "reports", ["node_id"])
        op.create_index("ix_reports_category", "reports", ["category"])
        op.create_index("ix_reports_created_at", "reports", ["created_at"])

    if "report_photos" not in table_names:
        op.create_table(
            "report_photos",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("report_id", sa.String(length=36), nullable=False),
            sa.Column("storage_key", sa.String(length=300), nullable=False),
            sa.Column("mime_type", sa.String(length=64), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("storage_key"),
        )
        op.create_index("ix_report_photos_report_id", "report_photos", ["report_id"])


def downgrade() -> None:
    op.drop_index("ix_report_photos_report_id", table_name="report_photos")
    op.drop_table("report_photos")
    op.drop_index("ix_reports_created_at", table_name="reports")
    op.drop_index("ix_reports_category", table_name="reports")
    op.drop_index("ix_reports_node_id", table_name="reports")
    op.drop_table("reports")
