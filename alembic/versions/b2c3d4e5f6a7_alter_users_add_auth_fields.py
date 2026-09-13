"""alter users add auth fields

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-13 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
    )
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.Enum(
                "reportante",
                "tecnico",
                "responsable_area",
                "coordinador",
                "administrador",
                "validador",
                name="roleenum",
            ),
            nullable=False,
            server_default="reportante",
        ),
    )
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "created_at")
    op.drop_column("users", "is_active")
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email")
