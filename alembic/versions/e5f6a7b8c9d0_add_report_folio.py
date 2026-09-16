"""add report folio column

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-15 22:00:00.000000

"""

from typing import Sequence, Union

import secrets

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FOLIO_TYPE = sa.String(length=32)
INDEX_NAME = "ix_reports_folio"


def _column_names(conn, table: str) -> set[str]:
    return {col["name"] for col in inspect(conn).get_columns(table)}


def _index_names(conn, table: str) -> set[str]:
    return {idx["name"] for idx in inspect(conn).get_indexes(table)}


def upgrade() -> None:
    conn = op.get_bind()
    columns = _column_names(conn, "reports")

    if "folio" not in columns:
        op.add_column("reports", sa.Column("folio", FOLIO_TYPE, nullable=True))

    rows = conn.execute(
        sa.text("SELECT id FROM reports WHERE folio IS NULL"),
    ).fetchall()
    used = {
        row[0]
        for row in conn.execute(
            sa.text("SELECT folio FROM reports WHERE folio IS NOT NULL"),
        ).fetchall()
    }
    for (row_id,) in rows:
        while True:
            folio = f"reporte-{secrets.token_hex(4)}"
            if folio not in used:
                used.add(folio)
                break
        conn.execute(
            sa.text("UPDATE reports SET folio = :folio WHERE id = :id"),
            {"folio": folio, "id": row_id},
        )

    op.alter_column(
        "reports",
        "folio",
        existing_type=FOLIO_TYPE,
        nullable=False,
    )

    if INDEX_NAME not in _index_names(conn, "reports"):
        op.create_index(INDEX_NAME, "reports", ["folio"], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    indexes = _index_names(conn, "reports")
    columns = _column_names(conn, "reports")

    if INDEX_NAME in indexes:
        op.drop_index(INDEX_NAME, table_name="reports")
    if "folio" in columns:
        op.drop_column("reports", "folio")
