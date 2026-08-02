"""Add workflow failure recovery metadata.

Revision ID: 0009
Revises: 0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflow_checkpoints",
        sa.Column(
            "parent_run_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "workflow_checkpoints",
        sa.Column("failure_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "workflow_checkpoints",
        sa.Column("retryable", sa.Boolean(), nullable=True),
    )
    op.create_index(
        "ix_workflow_checkpoints_parent_run_id",
        "workflow_checkpoints",
        ["parent_run_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workflow_checkpoints_parent_run_id",
        table_name="workflow_checkpoints",
    )
    op.drop_column("workflow_checkpoints", "retryable")
    op.drop_column("workflow_checkpoints", "failure_reason")
    op.drop_column("workflow_checkpoints", "parent_run_id")
