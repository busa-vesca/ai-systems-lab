"""Create tool executions table.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tool_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("output", postgresql.JSONB(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "latency_ms >= 0", name="ck_tool_executions_latency"
        ),
        sa.CheckConstraint(
            "status IN ('succeeded', 'failed')",
            name="ck_tool_executions_status",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["prediction_id"], ["model_predictions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tool_executions_incident_id",
        "tool_executions",
        ["incident_id"],
    )
    op.create_index(
        "ix_tool_executions_prediction_id",
        "tool_executions",
        ["prediction_id"],
    )
    op.create_index(
        "ix_tool_executions_tool_name",
        "tool_executions",
        ["tool_name"],
    )
    op.create_index(
        "ix_tool_executions_created_at",
        "tool_executions",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tool_executions_created_at", table_name="tool_executions"
    )
    op.drop_index(
        "ix_tool_executions_tool_name", table_name="tool_executions"
    )
    op.drop_index(
        "ix_tool_executions_prediction_id", table_name="tool_executions"
    )
    op.drop_index(
        "ix_tool_executions_incident_id", table_name="tool_executions"
    )
    op.drop_table("tool_executions")
