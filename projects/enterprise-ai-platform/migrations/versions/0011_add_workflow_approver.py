"""Record the user who approved a workflow.

Revision ID: 0011
Revises: 0010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflow_checkpoints",
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_workflow_checkpoints_approved_by_users",
        "workflow_checkpoints",
        "users",
        ["approved_by"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_workflow_checkpoints_approved_by",
        "workflow_checkpoints",
        ["approved_by"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workflow_checkpoints_approved_by",
        table_name="workflow_checkpoints",
    )
    op.drop_constraint(
        "fk_workflow_checkpoints_approved_by_users",
        "workflow_checkpoints",
        type_="foreignkey",
    )
    op.drop_column("workflow_checkpoints", "approved_by")
