"""Market coordinate columns for the geographic map layer.

Coordinates are NEVER fabricated: all three columns stay NULL until a
verified source (geocoded OpenStreetMap result, stored with provenance in
coordinate_source) provides them. Markets without coordinates are excluded
from map markers while remaining fully available in Market Intelligence.

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("geo_markets", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("geo_markets", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column(
        "geo_markets",
        sa.Column("coordinate_source", sa.String(64), nullable=False, server_default=""),
    )
    op.add_column(
        "geo_markets",
        sa.Column("coordinates_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_geo_markets_coords", "geo_markets", ["latitude", "longitude"])


def downgrade() -> None:
    op.drop_index("ix_geo_markets_coords", table_name="geo_markets")
    op.drop_column("geo_markets", "coordinates_updated_at")
    op.drop_column("geo_markets", "coordinate_source")
    op.drop_column("geo_markets", "longitude")
    op.drop_column("geo_markets", "latitude")
