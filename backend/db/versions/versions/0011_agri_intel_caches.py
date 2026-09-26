"""Agricultural intelligence caches + market price district index.

- soil_cache / crop_context_cache tables (reversible).
- Composite index on market_prices(district, arrival_date, commodity) so
  district crop-mix aggregation stays fast over 500k+ rows.

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "soil_cache",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lat_key", sa.Float(), nullable=False),
        sa.Column("lng_key", sa.Float(), nullable=False),
        sa.Column("property", sa.String(32), nullable=False),
        sa.Column("depth", sa.String(16), nullable=False, server_default="0-5cm"),
        sa.Column("mean", sa.Float(), nullable=True),
        sa.Column("uncertainty", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=False, server_default=""),
        sa.Column("source", sa.String(64), nullable=False, server_default="soilgrids/wcs"),
        sa.Column("source_version", sa.String(64), nullable=False, server_default=""),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lat_key", "lng_key", "property", "depth",
                            name="uq_soil_cache_cell_prop"),
    )
    op.create_index("ix_soil_cache_cell", "soil_cache", ["lat_key", "lng_key"])
    op.create_table(
        "crop_context_cache",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("district", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("data_year", sa.String(16), nullable=False, server_default=""),
        sa.Column("source", sa.String(64), nullable=False, server_default="agmarknet"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("district", "state", name="uq_crop_ctx_district"),
    )
    op.create_index("ix_market_prices_district_date",
                    "market_prices", ["district", "arrival_date", "commodity"])


def downgrade() -> None:
    op.drop_index("ix_market_prices_district_date", table_name="market_prices")
    op.drop_table("crop_context_cache")
    op.drop_index("ix_soil_cache_cell", table_name="soil_cache")
    op.drop_table("soil_cache")
