"""incident category assignment and status workflow

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-09-26 12:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "g7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_STATUSES = (
    "reportada",
    "validada",
    "asignada",
    "en_progreso",
    "en_validacion",
    "resuelta",
    "cerrada",
    "bloqueada",
    "reabierta",
)

CATEGORIES = (
    ("infraestructura", "Infraestructura"),
    ("electricidad", "Electricidad"),
    ("agua", "Agua"),
    ("ti", "TI"),
    ("mobiliario", "Mobiliario"),
    ("limpieza", "Limpieza"),
    ("seguridad", "Seguridad"),
    ("climatizacion", "Climatización"),
    ("otro", "Otro"),
)

CATEGORY_ENUM = sa.Enum(*[code for code, _name in CATEGORIES], name="incidentcategoryenum")
STATUS_ENUM = sa.Enum(*NEW_STATUSES, name="reportstatusenum")


def upgrade() -> None:
    op.create_table(
        "specialties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", CATEGORY_ENUM, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("category"),
    )
    op.create_index("ix_specialties_code", "specialties", ["code"], unique=True)

    for code, name in CATEGORIES:
        op.execute(
            sa.text(
                "INSERT INTO specialties (code, name, category) "
                "SELECT :code, :name, :category FROM DUAL "
                "WHERE NOT EXISTS (SELECT 1 FROM specialties WHERE code = :code)"
            ).bindparams(code=code, name=name, category=code)
        )

    op.add_column("reports", sa.Column("category", CATEGORY_ENUM, nullable=True))
    op.add_column("reports", sa.Column("specialty_id", sa.Integer(), nullable=True))
    op.add_column("reports", sa.Column("assignee_id", sa.Integer(), nullable=True))
    op.add_column("reports", sa.Column("assigned_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_reports_specialty_id",
        "reports",
        "specialties",
        ["specialty_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_reports_assignee_id",
        "reports",
        "users",
        ["assignee_id"],
        ["id"],
    )
    op.create_index("ix_reports_specialty_id", "reports", ["specialty_id"], unique=False)
    op.create_index("ix_reports_assignee_id", "reports", ["assignee_id"], unique=False)

    op.execute("ALTER TABLE reports MODIFY status VARCHAR(32) NOT NULL")
    op.execute(
        """
        UPDATE reports
        SET status = CASE
            WHEN status = 'creado' THEN 'reportada'
            WHEN status = 'resuelto' THEN 'resuelta'
            WHEN status = 'en_revision' AND awaiting_validation = 1 THEN 'en_validacion'
            WHEN status = 'en_revision' THEN 'validada'
            ELSE status
        END
        """
    )
    op.execute(
        "ALTER TABLE reports MODIFY status "
        "ENUM('reportada','validada','asignada','en_progreso','en_validacion',"
        "'resuelta','cerrada','bloqueada','reabierta') "
        "NOT NULL DEFAULT 'reportada'"
    )

    op.create_table(
        "report_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("assignee_id", sa.Integer(), nullable=False),
        sa.Column("assigned_by_id", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("status", STATUS_ENUM, nullable=False),
        sa.Column("specialty_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.ForeignKeyConstraint(["specialty_id"], ["specialties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_assignments_report_id", "report_assignments", ["report_id"])
    op.create_index("ix_report_assignments_assignee_id", "report_assignments", ["assignee_id"])
    op.create_index("ix_report_assignments_specialty_id", "report_assignments", ["specialty_id"])

    op.create_table(
        "report_status_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("from_status", STATUS_ENUM, nullable=False),
        sa.Column("to_status", STATUS_ENUM, nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_status_events_report_id", "report_status_events", ["report_id"])
    op.create_index("ix_report_status_events_actor_id", "report_status_events", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_report_status_events_actor_id", table_name="report_status_events")
    op.drop_index("ix_report_status_events_report_id", table_name="report_status_events")
    op.drop_table("report_status_events")

    op.drop_index("ix_report_assignments_specialty_id", table_name="report_assignments")
    op.drop_index("ix_report_assignments_assignee_id", table_name="report_assignments")
    op.drop_index("ix_report_assignments_report_id", table_name="report_assignments")
    op.drop_table("report_assignments")

    op.execute("ALTER TABLE reports MODIFY status VARCHAR(32) NOT NULL")
    op.execute(
        """
        UPDATE reports
        SET status = CASE
            WHEN status = 'reportada' THEN 'creado'
            WHEN status IN ('resuelta', 'cerrada') THEN 'resuelto'
            ELSE 'en_revision'
        END
        """
    )
    op.execute(
        "ALTER TABLE reports MODIFY status "
        "ENUM('creado','en_revision','resuelto') NOT NULL DEFAULT 'creado'"
    )

    op.drop_index("ix_reports_assignee_id", table_name="reports")
    op.drop_index("ix_reports_specialty_id", table_name="reports")
    op.drop_constraint("fk_reports_assignee_id", "reports", type_="foreignkey")
    op.drop_constraint("fk_reports_specialty_id", "reports", type_="foreignkey")
    op.drop_column("reports", "assigned_at")
    op.drop_column("reports", "assignee_id")
    op.drop_column("reports", "specialty_id")
    op.drop_column("reports", "category")

    op.drop_index("ix_specialties_code", table_name="specialties")
    op.drop_table("specialties")
