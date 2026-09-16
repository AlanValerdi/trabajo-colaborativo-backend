"""user roles table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-16 01:15:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLE_VALUES = (
    "reportante",
    "tecnico",
    "responsable_area",
    "coordinador",
    "administrador",
    "validador",
)


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def upgrade() -> None:
    if not _table_exists("user_roles"):
        op.create_table(
            "user_roles",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column(
                "role",
                sa.Enum(*ROLE_VALUES, name="roleenum"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "role"),
        )

    if _column_exists("users", "role"):
        op.execute(
            """
            INSERT INTO user_roles (user_id, role)
            SELECT u.id, u.role
            FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM user_roles ur
                WHERE ur.user_id = u.id AND ur.role = u.role
            )
            """
        )
        op.drop_column("users", "role")


def downgrade() -> None:
    if not _column_exists("users", "role"):
        op.add_column(
            "users",
            sa.Column(
                "role",
                sa.Enum(*ROLE_VALUES, name="roleenum"),
                nullable=False,
                server_default="reportante",
            ),
        )
        op.execute(
            """
            UPDATE users u
            SET role = (
                SELECT ur.role
                FROM user_roles ur
                WHERE ur.user_id = u.id
                ORDER BY ur.role
                LIMIT 1
            )
            """
        )

    if _table_exists("user_roles"):
        op.drop_table("user_roles")
