"""market geography catalog (source-backed states/districts/markets).

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "geo_states",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("source_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("source_id", name="uq_geo_states_source"),
    )
    op.create_table(
        "geo_districts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("source_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False, index=True),
        sa.Column("state_id", sa.Integer(), nullable=False, index=True),
        sa.Column("state_name", sa.String(100), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("source_id", name="uq_geo_districts_source"),
    )
    op.create_index(
        "ix_geo_districts_state_name", "geo_districts", ["state_name", "name"]
    )
    op.create_table(
        "geo_markets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("source_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("district_id", sa.Integer(), nullable=True, index=True),
        sa.Column(
            "district_name", sa.String(100), nullable=False, server_default=""
        ),
        sa.Column("state_id", sa.Integer(), nullable=True, index=True),
        sa.Column(
            "state_name", sa.String(100), nullable=False, server_default=""
        ),
        sa.Column("category", sa.String(100), nullable=False, server_default=""),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("source_id", name="uq_geo_markets_source"),
    )
    op.create_index(
        "ix_geo_markets_state_district",
        "geo_markets",
        ["state_name", "district_name", "name"],
    )


def downgrade() -> None:
    op.drop_table("geo_markets")
    op.drop_table("geo_districts")
    op.drop_table("geo_states")
