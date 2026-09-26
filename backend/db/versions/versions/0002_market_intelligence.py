"""market intelligence: provenance columns, natural key, ingestion audit.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "market_prices",
        sa.Column("grade", sa.String(100), nullable=True),
    )
    op.add_column(
        "market_prices",
        sa.Column("source_resource_id", sa.String(64), nullable=True),
    )
    op.add_column(
        "market_prices",
        sa.Column(
            "raw_record",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "market_prices",
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.add_column(
        "market_prices",
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Idempotent natural key: one row per observed dimension combination.
    # PostgreSQL treats NULL as distinct, so legacy NULL dimensions are
    # backfilled to "" first; all new writes normalize to "" before storage.
    for column in ("district", "variety", "grade"):
        op.execute(
            sa.text(
                f"UPDATE market_prices SET {column} = '' WHERE {column} IS NULL"
            )
        )
    op.create_unique_constraint(
        "uq_market_prices_observation",
        "market_prices",
        ["state", "district", "market", "commodity", "variety", "grade", "arrival_date"],
    )

    # Primary V1 query patterns.
    op.create_index(
        "ix_market_prices_state_district_commodity_date",
        "market_prices",
        ["state", "district", "commodity", "arrival_date"],
    )
    op.create_index(
        "ix_market_prices_market_date",
        "market_prices",
        ["market", "arrival_date"],
    )

    op.create_table(
        "market_ingestions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("resource_id", sa.String(64), nullable=False),
        sa.Column("state_filter", sa.String(100), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stored_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("min_observation_date", sa.Date(), nullable=True),
        sa.Column("max_observation_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("error", sa.String(2000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("market_ingestions")
    op.drop_index("ix_market_prices_market_date", table_name="market_prices")
    op.drop_index(
        "ix_market_prices_state_district_commodity_date", table_name="market_prices"
    )
    op.drop_constraint(
        "uq_market_prices_observation", "market_prices", type_="unique"
    )
    op.drop_column("market_prices", "ingested_at")
    op.drop_column("market_prices", "fetched_at")
    op.drop_column("market_prices", "raw_record")
    op.drop_column("market_prices", "source_resource_id")
    op.drop_column("market_prices", "grade")
