"""Market arrivals on mandi observations (same grain, no semantic change).

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "market_prices",
        sa.Column("arrivals", sa.Float(), nullable=True),
    )
    op.add_column(
        "market_prices",
        sa.Column("arrival_unit", sa.String(50), nullable=True),
    )
    op.create_index(
        "ix_market_prices_commodity_arrival_date",
        "market_prices",
        ["commodity", "arrival_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_market_prices_commodity_arrival_date", table_name="market_prices")
    op.drop_column("market_prices", "arrival_unit")
    op.drop_column("market_prices", "arrivals")
