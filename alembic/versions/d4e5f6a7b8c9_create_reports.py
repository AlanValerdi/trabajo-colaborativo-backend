"""create reports table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-13 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("campus_label", sa.String(length=255), nullable=False),
        sa.Column("space_label", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("creado", "en_revision", "resuelto", name="reportstatusenum"),
            nullable=False,
            server_default="creado",
        ),
        sa.Column("image_url", sa.String(length=1024), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("classified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "priority",
            sa.Enum("baja", "media", "alta", name="reportpriorityenum"),
            nullable=True,
        ),
        sa.Column("awaiting_validation", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_reports_author_id", "reports", ["author_id"])


def downgrade() -> None:
    op.drop_index("ix_reports_author_id", table_name="reports")
    op.drop_table("reports")
