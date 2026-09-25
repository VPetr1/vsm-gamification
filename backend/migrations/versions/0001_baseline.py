"""Baseline: schema as created by the pre-Alembic create_all().

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("depot", sa.String(200), nullable=False),
        sa.Column("brigade", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("graph", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("scenario_id", sa.String(36), sa.ForeignKey("scenarios.id"), nullable=False),
        sa.Column("current_node", sa.String(100), nullable=False),
        sa.Column("loyalty", sa.Integer(), nullable=False),
        sa.Column("safety", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("in_progress", "finished", name="attempt_status"), nullable=False),
        sa.Column("ending_summary", sa.Text(), nullable=True),
        sa.Column("node_shown_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "choice_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("attempt_id", sa.String(36), sa.ForeignKey("attempts.id"), nullable=False),
        sa.Column("node_id", sa.String(100), nullable=False),
        sa.Column("choice_id", sa.String(100), nullable=True),
        sa.Column("timed_out", sa.Boolean(), nullable=False),
        sa.Column("loyalty_delta", sa.Integer(), nullable=False),
        sa.Column("safety_delta", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("choice_logs")
    op.drop_table("attempts")
    op.drop_table("scenarios")
    op.drop_table("employees")
    sa.Enum(name="attempt_status").drop(op.get_bind(), checkfirst=True)
