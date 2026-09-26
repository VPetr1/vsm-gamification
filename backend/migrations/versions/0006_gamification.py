"""XP from best scores, achievements, notifications, synthetic results.

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("attempts") as batch:
        batch.add_column(sa.Column("score", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("xp_gained", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "scenario_bests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("scenario_id", sa.String(36), sa.ForeignKey("scenarios.id"), nullable=False),
        sa.Column("best_score", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.String(36), sa.ForeignKey("attempts.id"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("employee_id", "scenario_id", name="uq_scenario_bests_employee_scenario"),
    )
    op.create_table(
        "employee_achievements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("achievement_id", sa.String(50), nullable=False),
        sa.Column("attempt_id", sa.String(36), sa.ForeignKey("attempts.id"), nullable=True),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("employee_id", "achievement_id", name="uq_employee_achievements_once"),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("link", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_employee_id", "notifications", ["employee_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_employee_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("employee_achievements")
    op.drop_table("scenario_bests")
    with op.batch_alter_table("attempts") as batch:
        batch.drop_column("is_synthetic")
        batch.drop_column("xp_gained")
        batch.drop_column("score")
