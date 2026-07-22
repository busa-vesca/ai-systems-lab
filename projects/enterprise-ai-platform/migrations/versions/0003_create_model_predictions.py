"""Create model predictions table.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("model_id", sa.String(length=200), nullable=False),
        sa.Column("model_revision", sa.String(length=64), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "latency_ms >= 0", name="ck_model_predictions_latency"
        ),
        sa.CheckConstraint(
            "score >= 0 AND score <= 1", name="ck_model_predictions_score"
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_model_predictions_incident_id",
        "model_predictions",
        ["incident_id"],
    )
    op.create_index(
        "ix_model_predictions_label", "model_predictions", ["label"]
    )
    op.create_index(
        "ix_model_predictions_created_at",
        "model_predictions",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_model_predictions_created_at", table_name="model_predictions"
    )
    op.drop_index(
        "ix_model_predictions_label", table_name="model_predictions"
    )
    op.drop_index(
        "ix_model_predictions_incident_id", table_name="model_predictions"
    )
    op.drop_table("model_predictions")
