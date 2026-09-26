"""Assistant provider usage accounting (OpenRouter tier budgets).

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assistant_provider_usage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(256), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=True),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_request_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usage_date", "provider", "model", name="uq_provider_usage_day_model"),
    )
    op.create_index("ix_assistant_provider_usage_date", "assistant_provider_usage", ["usage_date"])
    op.create_index("ix_assistant_provider_usage_provider", "assistant_provider_usage", ["provider"])


def downgrade() -> None:
    op.drop_index("ix_assistant_provider_usage_provider", table_name="assistant_provider_usage")
    op.drop_index("ix_assistant_provider_usage_date", table_name="assistant_provider_usage")
    op.drop_table("assistant_provider_usage")
