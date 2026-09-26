"""initial schema: users, farms, plots, disease, weather, market, schemes, etc.

Revision ID: 0001
Revises:
Create Date: 2026-01-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    op.execute('CREATE EXTENSION IF NOT EXISTS h3')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("phone", sa.String(20), unique=True, nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("farmer", "analyst", "admin", "superadmin", name="user_role"), nullable=False, server_default="farmer"),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "farms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="India"),
        sa.Column("total_area_hectares", sa.Float(), nullable=False, server_default="0"),
        sa.Column("soil_type", sa.String(100), nullable=True),
        sa.Column("irrigation_type", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "plots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("crop_type", sa.String(100), nullable=True),
        sa.Column("crop_variety", sa.String(100), nullable=True),
        sa.Column("sowing_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expected_harvest_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("area_hectares", sa.Float(), nullable=False, server_default="0"),
        sa.Column("geometry", geoalchemy2.Geography(geometry_type="POLYGON", srid=4326), nullable=True),
        sa.Column("centroid", geoalchemy2.Geography(geometry_type="POINT", srid=4326), nullable=True),
        sa.Column("h3_index", sa.String(50), nullable=False, index=True),
        sa.Column("h3_resolution", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("soil_ph", sa.Float(), nullable=True),
        sa.Column("soil_moisture", sa.Float(), nullable=True),
        sa.Column("irrigation_type", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "disease_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("plot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("h3_spatial_index", sa.String(50), nullable=False, index=True),
        sa.Column("detected_disease", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("detections", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("severity", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "disease_detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("disease_log_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("disease_logs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("class_name", sa.String(255), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("bbox", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "weather_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("plot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plots.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("h3_index", sa.String(50), nullable=False, index=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("feels_like", sa.Float(), nullable=True),
        sa.Column("humidity", sa.Integer(), nullable=True),
        sa.Column("pressure", sa.Integer(), nullable=True),
        sa.Column("wind_speed", sa.Float(), nullable=True),
        sa.Column("wind_deg", sa.Integer(), nullable=True),
        sa.Column("cloud_cover", sa.Integer(), nullable=True),
        sa.Column("visibility", sa.Integer(), nullable=True),
        sa.Column("weather_main", sa.String(100), nullable=True),
        sa.Column("weather_description", sa.String(255), nullable=True),
        sa.Column("rain_1h", sa.Float(), nullable=False, server_default="0"),
        sa.Column("snow_1h", sa.Float(), nullable=False, server_default="0"),
        sa.Column("raw_response", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "weather_forecasts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("h3_index", sa.String(50), nullable=False, index=True),
        sa.Column("forecast_data", postgresql.JSONB(), nullable=False),
        sa.Column("forecasted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "market_prices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("commodity", sa.String(255), nullable=False, index=True),
        sa.Column("variety", sa.String(255), nullable=True),
        sa.Column("market", sa.String(255), nullable=False, index=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=False, index=True),
        sa.Column("min_price", sa.Float(), nullable=False),
        sa.Column("max_price", sa.Float(), nullable=False),
        sa.Column("modal_price", sa.Float(), nullable=False),
        sa.Column("price_per_unit", sa.String(50), nullable=False, server_default="INR/quintal"),
        sa.Column("arrival_date", sa.Date(), nullable=False, index=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="AGMARKNET"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "government_schemes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scheme_name", sa.String(255), nullable=False, index=True),
        sa.Column("scheme_code", sa.String(50), unique=True, nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("ministry", sa.String(255), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("state_jurisdiction", sa.String(100), nullable=True, index=True),
        sa.Column("eligibility_criteria", sa.Text(), nullable=True),
        sa.Column("benefits", sa.Text(), nullable=True),
        sa.Column("application_process", sa.Text(), nullable=True),
        sa.Column("documents_required", sa.Text(), nullable=True),
        sa.Column("funding_pattern", sa.String(255), nullable=True),
        sa.Column("beneficiary_type", sa.String(100), nullable=True),
        sa.Column("category", sa.String(100), nullable=True, index=True),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("website_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(50), nullable=False, server_default="info"),
        sa.Column("channel", sa.String(50), nullable=False, server_default="in_app"),
        sa.Column("reference_type", sa.String(100), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_sent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "analytics_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("event_name", sa.String(255), nullable=False),
        sa.Column("properties", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(255), nullable=True),
        sa.Column("changes", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_index("ix_plots_geometry_gist", "plots", [sa.text("geometry")], postgresql_using="gist")
    op.create_index("ix_plots_centroid_gist", "plots", [sa.text("centroid")], postgresql_using="gist")
    op.create_index("ix_market_prices_commodity_state_date", "market_prices", ["commodity", "state", "arrival_date"])
    op.create_index("ix_disease_logs_h3_created", "disease_logs", ["h3_spatial_index", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_disease_logs_h3_created", table_name="disease_logs")
    op.drop_index("ix_market_prices_commodity_state_date", table_name="market_prices")
    op.drop_index("ix_plots_centroid_gist", table_name="plots")
    op.drop_index("ix_plots_geometry_gist", table_name="plots")

    op.drop_table("audit_logs")
    op.drop_table("analytics_events")
    op.drop_table("notifications")
    op.drop_table("government_schemes")
    op.drop_table("market_prices")
    op.drop_table("weather_forecasts")
    op.drop_table("weather_records")
    op.drop_table("disease_detections")
    op.drop_table("disease_logs")
    op.drop_table("plots")
    op.drop_table("farms")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS user_role")
