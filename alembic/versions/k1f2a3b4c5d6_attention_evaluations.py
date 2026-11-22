"""HU-30: one immutable attention evaluation per incident."""
from alembic import op
import sqlalchemy as sa

revision = 'k1f2a3b4c5d6'
down_revision = 'j0e1f2a3b4c5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'attention_evaluations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('report_id', sa.Integer(), sa.ForeignKey('reports.id'), nullable=False),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('report_id', name='uq_attention_evaluation_report'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_attention_rating'),
    )


def downgrade():
    op.drop_table('attention_evaluations')
