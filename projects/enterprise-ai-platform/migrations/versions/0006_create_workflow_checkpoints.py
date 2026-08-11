"""Create workflow checkpoints.

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workflow_checkpoints",
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("step", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_workflow_checkpoints_version",
        ),
        sa.CheckConstraint(
            "step IN ("
            "'received', 'classified', 'policy_checked', "
            "'awaiting_approval', 'approved', 'tool_executed', "
            "'skipped', 'completed', 'failed'"
            ")",
            name="ck_workflow_checkpoints_step",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("run_id", "version"),
    )
    op.create_index(
        "ix_workflow_checkpoints_incident_id",
        "workflow_checkpoints",
        ["incident_id"],
    )
    op.create_index(
        "ix_workflow_checkpoints_step",
        "workflow_checkpoints",
        ["step"],
    )
    op.create_index(
        "ix_workflow_checkpoints_updated_at",
        "workflow_checkpoints",
        ["updated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workflow_checkpoints_updated_at",
        table_name="workflow_checkpoints",
    )
    op.drop_index(
        "ix_workflow_checkpoints_step",
        table_name="workflow_checkpoints",
    )
    op.drop_index(
        "ix_workflow_checkpoints_incident_id",
        table_name="workflow_checkpoints",
    )
    op.drop_table("workflow_checkpoints")
