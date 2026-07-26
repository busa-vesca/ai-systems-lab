"""Add workflow resume context.

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflow_checkpoints",
        sa.Column(
            "prediction_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "workflow_checkpoints",
        sa.Column(
            "tool_execution_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "workflow_checkpoints",
        sa.Column("skipped_reason", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_workflow_checkpoints_prediction_id",
        "workflow_checkpoints",
        "model_predictions",
        ["prediction_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_workflow_checkpoints_tool_execution_id",
        "workflow_checkpoints",
        "tool_executions",
        ["tool_execution_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_workflow_checkpoints_tool_execution_id",
        "workflow_checkpoints",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_workflow_checkpoints_prediction_id",
        "workflow_checkpoints",
        type_="foreignkey",
    )
    op.drop_column("workflow_checkpoints", "skipped_reason")
    op.drop_column("workflow_checkpoints", "tool_execution_id")
    op.drop_column("workflow_checkpoints", "prediction_id")
