"""add critical report priority

Revision ID: k1f2a3b4c5d6
Revises: j0e1f2a3b4c5
Create Date: 2026-11-22

"""

from typing import Sequence, Union

from alembic import op

revision: str = "k1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "j0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE reports MODIFY priority "
        "ENUM('baja','media','alta','critica') NULL"
    )


def downgrade() -> None:
    op.execute("UPDATE reports SET priority = 'alta' WHERE priority = 'critica'")
    op.execute(
        "ALTER TABLE reports MODIFY priority "
        "ENUM('baja','media','alta') NULL"
    )
