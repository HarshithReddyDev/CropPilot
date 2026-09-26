"""national market filtering indexes.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-21
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Latest-per-group lookups filtered by state + market.
    op.create_index(
        "ix_market_prices_state_market_date",
        "market_prices",
        ["state", "market", "arrival_date"],
    )
    # Comparison lookups: one commodity across markets over time.
    op.create_index(
        "ix_market_prices_market_commodity_date",
        "market_prices",
        ["market", "commodity", "arrival_date"],
    )
    # National commodity views and history without geography filters.
    op.create_index(
        "ix_market_prices_commodity_date",
        "market_prices",
        ["commodity", "arrival_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_market_prices_commodity_date", table_name="market_prices")
    op.drop_index(
        "ix_market_prices_market_commodity_date", table_name="market_prices"
    )
    op.drop_index("ix_market_prices_state_market_date", table_name="market_prices")
