"""catalog tables campus faculty location

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-09-16 13:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED_CAMPUSES = ("CU", "CCU", "CU2")


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
    if not _table_exists("campuses"):
        op.create_table(
            "campuses",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(length=32), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
        )
        op.create_index("ix_campuses_code", "campuses", ["code"], unique=True)

    if not _table_exists("faculties"):
        op.create_table(
            "faculties",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("campus_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.ForeignKeyConstraint(["campus_id"], ["campuses.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_faculties_campus_id", "faculties", ["campus_id"], unique=False)

    if not _table_exists("locations"):
        op.create_table(
            "locations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("faculty_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.ForeignKeyConstraint(["faculty_id"], ["faculties.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_locations_faculty_id", "locations", ["faculty_id"], unique=False)

    for code in SEED_CAMPUSES:
        op.execute(
            sa.text(
                "INSERT INTO campuses (code, name) "
                "SELECT :code, :name FROM DUAL "
                "WHERE NOT EXISTS (SELECT 1 FROM campuses WHERE code = :code)"
            ).bindparams(code=code, name=code)
        )

    if not _column_exists("reports", "faculty_label"):
        op.add_column(
            "reports",
            sa.Column("faculty_label", sa.String(length=255), nullable=False, server_default=""),
        )

    if not _column_exists("reports", "campus_id"):
        op.add_column("reports", sa.Column("campus_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_reports_campus_id",
            "reports",
            "campuses",
            ["campus_id"],
            ["id"],
        )
        op.create_index("ix_reports_campus_id", "reports", ["campus_id"], unique=False)

    if not _column_exists("reports", "faculty_id"):
        op.add_column("reports", sa.Column("faculty_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_reports_faculty_id",
            "reports",
            "faculties",
            ["faculty_id"],
            ["id"],
        )
        op.create_index("ix_reports_faculty_id", "reports", ["faculty_id"], unique=False)

    if not _column_exists("reports", "location_id"):
        op.add_column("reports", sa.Column("location_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_reports_location_id",
            "reports",
            "locations",
            ["location_id"],
            ["id"],
        )
        op.create_index("ix_reports_location_id", "reports", ["location_id"], unique=False)

    op.execute(
        """
        UPDATE reports
        SET campus_id = (SELECT MIN(id) FROM campuses)
        WHERE campus_id IS NULL
        """
    )


def downgrade() -> None:
    if _column_exists("reports", "location_id"):
        op.drop_index("ix_reports_location_id", table_name="reports")
        op.drop_constraint("fk_reports_location_id", "reports", type_="foreignkey")
        op.drop_column("reports", "location_id")

    if _column_exists("reports", "faculty_id"):
        op.drop_index("ix_reports_faculty_id", table_name="reports")
        op.drop_constraint("fk_reports_faculty_id", "reports", type_="foreignkey")
        op.drop_column("reports", "faculty_id")

    if _column_exists("reports", "campus_id"):
        op.drop_index("ix_reports_campus_id", table_name="reports")
        op.drop_constraint("fk_reports_campus_id", "reports", type_="foreignkey")
        op.drop_column("reports", "campus_id")

    if _column_exists("reports", "faculty_label"):
        op.drop_column("reports", "faculty_label")

    if _table_exists("locations"):
        op.drop_index("ix_locations_faculty_id", table_name="locations")
        op.drop_table("locations")

    if _table_exists("faculties"):
        op.drop_index("ix_faculties_campus_id", table_name="faculties")
        op.drop_table("faculties")

    if _table_exists("campuses"):
        op.drop_index("ix_campuses_code", table_name="campuses")
        op.drop_table("campuses")
