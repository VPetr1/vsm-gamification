"""Demo accounts with roles and server-side sessions.

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("employees") as batch:
        batch.add_column(sa.Column("login", sa.String(50), nullable=True))
        batch.add_column(sa.Column("password_hash", sa.String(200), nullable=True))
        batch.add_column(sa.Column("role", sa.String(20), nullable=False, server_default="conductor"))
        batch.add_column(sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.create_unique_constraint("uq_employees_login", ["login"])

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_auth_sessions_token_hash"),
    )


def downgrade() -> None:
    op.drop_table("auth_sessions")
    with op.batch_alter_table("employees") as batch:
        batch.drop_constraint("uq_employees_login", type_="unique")
        batch.drop_column("is_synthetic")
        batch.drop_column("role")
        batch.drop_column("password_hash")
        batch.drop_column("login")
