"""Add attempt count to tool executions.

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tool_executions",
        sa.Column(
            "attempts",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_tool_executions_attempts",
        "tool_executions",
        "attempts >= 1",
    )
    op.alter_column("tool_executions", "attempts", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "ck_tool_executions_attempts",
        "tool_executions",
        type_="check",
    )
    op.drop_column("tool_executions", "attempts")
