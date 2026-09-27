"""add diagnoses and work logs

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-09-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "i9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "h8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _table_exists("diagnoses"):
        op.create_table(
            "diagnoses",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("report_id", sa.Integer(), nullable=False),
            sa.Column("author_id", sa.Integer(), nullable=False),
            sa.Column("evaluation", sa.Text(), nullable=False),
            sa.Column("root_cause", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
            sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("report_id"),
        )

        op.create_index(
            "ix_diagnoses_report_id",
            "diagnoses",
            ["report_id"],
            unique=True,
        )

        op.create_index(
            "ix_diagnoses_author_id",
            "diagnoses",
            ["author_id"],
            unique=False,
        )

    if not _table_exists("work_logs"):
        op.create_table(
            "work_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("report_id", sa.Integer(), nullable=False),
            sa.Column("author_id", sa.Integer(), nullable=False),
            sa.Column("tasks", sa.Text(), nullable=False),
            sa.Column("materials", sa.Text(), nullable=False),
            sa.Column("time_minutes", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
            sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

        op.create_index(
            "ix_work_logs_report_id",
            "work_logs",
            ["report_id"],
            unique=False,
        )

        op.create_index(
            "ix_work_logs_author_id",
            "work_logs",
            ["author_id"],
            unique=False,
        )


def downgrade() -> None:
    if _table_exists("work_logs"):
        op.drop_index("ix_work_logs_author_id", table_name="work_logs")
        op.drop_index("ix_work_logs_report_id", table_name="work_logs")
        op.drop_table("work_logs")

    if _table_exists("diagnoses"):
        op.drop_index("ix_diagnoses_author_id", table_name="diagnoses")
        op.drop_index("ix_diagnoses_report_id", table_name="diagnoses")
        op.drop_table("diagnoses")