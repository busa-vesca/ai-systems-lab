"""Add tool execution idempotency keys.

Revision ID: 0008
Revises: 0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tool_executions",
        sa.Column("idempotency_key", sa.String(length=200), nullable=True),
    )
    op.execute(
        "UPDATE tool_executions "
        "SET idempotency_key = 'legacy:' || id::text"
    )
    op.alter_column(
        "tool_executions",
        "idempotency_key",
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_tool_executions_idempotency_key",
        "tool_executions",
        ["idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_tool_executions_idempotency_key",
        "tool_executions",
        type_="unique",
    )
    op.drop_column("tool_executions", "idempotency_key")
