"""Multi-source market data layer: registry, masters, canonical observations.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-22
"""

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _stamps():
    return [
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
    ]


def _provenance_extra():
    return [
        sa.Column(
            "raw_payload",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    ]


SOURCES = [
    {
        "code": "AGMARKNET",
        "name": "AGMARKNET Direct",
        "organization": "Directorate of Marketing and Inspection",
        "category": "mandi",
        "base_url": "https://api.agmarknet.gov.in/v1/",
        "source_type": "api",
        "access_type": "public",
        "attribution_text": "Mandi price observations from AGMARKNET.",
        "enabled": True,
    },
    {
        "code": "ENAM",
        "name": "eNAM",
        "organization": "Small Farmers Agribusiness Consortium",
        "category": "auction",
        "base_url": "https://enam.gov.in/",
        "source_type": "portal",
        "access_type": "requires_access",
        "attribution_text": "Electronic agricultural trading platform.",
        "enabled": False,
    },
    {
        "code": "DCA_PMD",
        "name": "DCA Price Monitoring System",
        "organization": "Department of Consumer Affairs",
        "category": "consumer",
        "base_url": "https://fcainfoweb.nic.in/",
        "source_type": "portal",
        "access_type": "no_stable_api",
        "attribution_text": "Daily retail and wholesale prices of essential commodities.",
        "enabled": False,
    },
    {
        "code": "DES_AGRI",
        "name": "DES Agricultural Prices",
        "organization": "Directorate of Economics and Statistics",
        "category": "statistics",
        "base_url": "https://desagri.gov.in/",
        "source_type": "portal",
        "access_type": "no_stable_api",
        "attribution_text": "Wholesale, retail, farm harvest and international price series.",
        "enabled": False,
    },
    {
        "code": "STATE_APMC",
        "name": "State APMC Portals",
        "organization": "Various state authorities",
        "category": "mandi",
        "base_url": "",
        "source_type": "registry",
        "access_type": "investigate",
        "attribution_text": "State-specific official market sources.",
        "enabled": False,
    },
    {
        "code": "TRADESTAT",
        "name": "TradeStat",
        "organization": "Ministry of Commerce (DGCIS data)",
        "category": "trade",
        "base_url": "https://tradestat.commerce.gov.in/",
        "source_type": "portal",
        "access_type": "no_stable_api",
        "attribution_text": "Monthly import/export statistics by HS code and country.",
        "enabled": False,
    },
    {
        "code": "NCDEX",
        "name": "NCDEX",
        "organization": "National Commodity and Derivatives Exchange",
        "category": "exchange",
        "base_url": "https://www.ncdex.com/",
        "source_type": "portal",
        "access_type": "licensed",
        "attribution_text": "Agricultural commodity derivatives market data.",
        "enabled": False,
    },
    {
        "code": "MCX",
        "name": "MCX",
        "organization": "Multi Commodity Exchange",
        "category": "exchange",
        "base_url": "https://www.mcxindia.com/",
        "source_type": "portal",
        "access_type": "licensed",
        "attribution_text": "Commodity derivatives market data.",
        "enabled": False,
    },
    {
        "code": "FCI",
        "name": "Food Corporation of India",
        "organization": "Food Corporation of India",
        "category": "procurement",
        "base_url": "https://fci.gov.in/",
        "source_type": "portal",
        "access_type": "document_only",
        "attribution_text": "Procurement and stock information.",
        "enabled": False,
    },
    {
        "code": "CACP_MSP",
        "name": "CACP MSP Notifications",
        "organization": "Commission for Agricultural Costs and Prices",
        "category": "procurement",
        "base_url": "https://cacp.dacnet.nic.in/",
        "source_type": "portal",
        "access_type": "document_only",
        "attribution_text": "Minimum support price notifications.",
        "enabled": False,
    },
]


def upgrade() -> None:
    op.create_table(
        "market_data_sources",
        *_stamps(),
        sa.Column("code", sa.String(32), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("organization", sa.String(255), nullable=False, server_default=""),
        sa.Column("category", sa.String(32), nullable=False, server_default=""),
        sa.Column("base_url", sa.String(500), nullable=False, server_default=""),
        sa.Column("source_type", sa.String(32), nullable=False, server_default=""),
        sa.Column("access_type", sa.String(32), nullable=False, server_default=""),
        sa.Column("attribution_text", sa.String(500), nullable=False, server_default=""),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "market_master",
        *_stamps(),
        sa.Column("display_name", sa.String(255), nullable=False, index=True),
        sa.Column("state", sa.String(100), nullable=False, server_default="", index=True),
        sa.Column("district", sa.String(100), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "source_market_mappings",
        *_stamps(),
        sa.Column("market_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("source_code", sa.String(32), nullable=False, index=True),
        sa.Column("source_market_id", sa.String(64), nullable=False),
        sa.Column("source_market_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "commodity_master",
        *_stamps(),
        sa.Column("display_name", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "source_commodity_mappings",
        *_stamps(),
        sa.Column("commodity_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("source_code", sa.String(32), nullable=False, index=True),
        sa.Column("source_commodity_id", sa.String(64), nullable=False, server_default=""),
        sa.Column("source_commodity_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="unmapped"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "consumer_prices",
        *_stamps(),
        sa.Column("source_code", sa.String(32), nullable=False, index=True),
        sa.Column("source_record_id", sa.String(128), nullable=False, server_default=""),
        sa.Column("centre", sa.String(255), nullable=False, index=True),
        sa.Column("commodity", sa.String(255), nullable=False, index=True),
        sa.Column("price_type", sa.String(32), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False, server_default=""),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("observation_date", sa.Date(), nullable=False, index=True),
        *_provenance_extra(),
    )
    op.create_table(
        "trade_observations",
        *_stamps(),
        sa.Column("source_code", sa.String(32), nullable=False, index=True),
        sa.Column("source_record_id", sa.String(128), nullable=False, server_default=""),
        sa.Column("market", sa.String(255), nullable=False, index=True),
        sa.Column("commodity", sa.String(255), nullable=False, index=True),
        sa.Column("variety", sa.String(255), nullable=True),
        sa.Column("grade", sa.String(100), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=False, server_default=""),
        sa.Column("trade_date", sa.Date(), nullable=False, index=True),
        sa.Column("trade_type", sa.String(32), nullable=False, server_default=""),
        *_provenance_extra(),
    )
    op.create_table(
        "agri_price_series",
        *_stamps(),
        sa.Column("source_code", sa.String(32), nullable=False, index=True),
        sa.Column("source_record_id", sa.String(128), nullable=False, server_default=""),
        sa.Column("series", sa.String(64), nullable=False, index=True),
        sa.Column("commodity", sa.String(255), nullable=False, index=True),
        sa.Column("geography", sa.String(255), nullable=False, server_default=""),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=False, server_default=""),
        sa.Column("observation_date", sa.Date(), nullable=False, index=True),
        *_provenance_extra(),
    )
    op.create_table(
        "trade_stats",
        *_stamps(),
        sa.Column("source_code", sa.String(32), nullable=False, index=True),
        sa.Column("source_record_id", sa.String(128), nullable=False, server_default=""),
        sa.Column("commodity", sa.String(255), nullable=False, index=True),
        sa.Column("hs_code", sa.String(16), nullable=False, server_default="", index=True),
        sa.Column("country", sa.String(255), nullable=False, server_default=""),
        sa.Column("region", sa.String(255), nullable=False, server_default=""),
        sa.Column("trade_type", sa.String(16), nullable=False),
        sa.Column("month", sa.Date(), nullable=False, index=True),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("quantity_unit", sa.String(32), nullable=False, server_default=""),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("value_unit", sa.String(32), nullable=False, server_default=""),
        *_provenance_extra(),
    )
    op.create_table(
        "exchange_observations",
        *_stamps(),
        sa.Column("source_code", sa.String(32), nullable=False, index=True),
        sa.Column("source_record_id", sa.String(128), nullable=False, server_default=""),
        sa.Column("instrument", sa.String(64), nullable=False, index=True),
        sa.Column("commodity", sa.String(255), nullable=False, index=True),
        sa.Column("contract", sa.String(64), nullable=False, server_default=""),
        sa.Column("expiry", sa.Date(), nullable=True),
        sa.Column("open", sa.Float(), nullable=True),
        sa.Column("high", sa.Float(), nullable=True),
        sa.Column("low", sa.Float(), nullable=True),
        sa.Column("close", sa.Float(), nullable=True),
        sa.Column("ltp", sa.Float(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("open_interest", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=False, server_default=""),
        sa.Column("observation_date", sa.Date(), nullable=False, index=True),
        *_provenance_extra(),
    )

    sources_table = sa.table(
        "market_data_sources",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String(32)),
        sa.column("name", sa.String(255)),
        sa.column("organization", sa.String(255)),
        sa.column("category", sa.String(32)),
        sa.column("base_url", sa.String(500)),
        sa.column("source_type", sa.String(32)),
        sa.column("access_type", sa.String(32)),
        sa.column("attribution_text", sa.String(500)),
        sa.column("enabled", sa.Boolean()),
    )
    op.bulk_insert(
        sources_table,
        [{**row, "id": uuid.uuid4()} for row in SOURCES],
    )


def downgrade() -> None:
    op.drop_table("exchange_observations")
    op.drop_table("trade_stats")
    op.drop_table("agri_price_series")
    op.drop_table("trade_observations")
    op.drop_table("consumer_prices")
    op.drop_table("source_commodity_mappings")
    op.drop_table("commodity_master")
    op.drop_table("source_market_mappings")
    op.drop_table("market_master")
    op.drop_table("market_data_sources")
