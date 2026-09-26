"""Multi-source layer tests: registry, masters, canonical observation tables."""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def source_session():
    from db.base import Base
    from models.market_sources import (
        AgriPriceSeries,
        CommodityMaster,
        ConsumerPrice,
        ExchangeObservation,
        MarketDataSource,
        MarketMaster,
        SourceCommodityMapping,
        SourceMarketMapping,
        TradeObservation,
        TradeStat,
    )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,  # type: ignore[arg-type]
            tables=[  # type: ignore[list-item]
                MarketDataSource.__table__,
                MarketMaster.__table__,
                SourceMarketMapping.__table__,
                CommodityMaster.__table__,
                SourceCommodityMapping.__table__,
                ConsumerPrice.__table__,
                TradeObservation.__table__,
                AgriPriceSeries.__table__,
                TradeStat.__table__,
                ExchangeObservation.__table__,
            ],
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


async def _seed_registry(session: AsyncSession):
    from models.market_sources import MarketDataSource

    session.add_all([
        MarketDataSource(code="AGMARKNET", name="AGMARKNET Direct",
                         organization="DMI", category="mandi",
                         base_url="https://api.agmarknet.gov.in/v1/",
                         source_type="api", access_type="public",
                         attribution_text="Mandi price observations.",
                         enabled=True),
        MarketDataSource(code="ENAM", name="eNAM",
                         organization="SFAC", category="auction",
                         base_url="https://enam.gov.in/",
                         source_type="portal", access_type="requires_access",
                         attribution_text="Electronic trading platform.",
                         enabled=False),
    ])
    await session.flush()


async def test_registry_lists_sources_with_capabilities(source_session):
    from services.source_registry import CAPABILITIES, list_sources

    await _seed_registry(source_session)
    rows = await list_sources(source_session)
    assert {r.code for r in rows} == {"AGMARKNET", "ENAM"}
    agm = next(r for r in rows if r.code == "AGMARKNET")
    assert agm.status == "IMPLEMENTED"
    assert "mandi price" in agm.provides
    assert agm.enabled is True
    enam = next(r for r in rows if r.code == "ENAM")
    assert enam.status == "REQUIRES_ACCESS"
    assert enam.enabled is False
    assert set(CAPABILITIES) >= {"AGMARKNET", "ENAM", "DCA_PMD", "DES_AGRI",
                                 "STATE_APMC", "TRADESTAT", "NCDEX", "MCX",
                                 "FCI", "CACP_MSP"}
    assert CAPABILITIES["FCI"]["status"] == "NOT_PRACTICAL"
    assert CAPABILITIES["CACP_MSP"]["status"] == "NOT_PRACTICAL"


async def test_registry_code_unique(source_session):
    from sqlalchemy.exc import IntegrityError

    from models.market_sources import MarketDataSource

    await _seed_registry(source_session)
    source_session.add(MarketDataSource(code="AGMARKNET", name="Dup"))
    with pytest.raises(IntegrityError):
        await source_session.flush()


async def test_market_master_not_collapsed_by_name(source_session):
    from models.market_sources import MarketMaster, SourceMarketMapping

    m1 = MarketMaster(display_name="Azadpur", state="Delhi", district="North Delhi")
    m2 = MarketMaster(display_name="Azadpur", state="Haryana", district="Sonipat")
    source_session.add_all([m1, m2])
    await source_session.flush()
    assert m1.id != m2.id
    source_session.add(SourceMarketMapping(
        market_id=m1.id, source_code="AGMARKNET",
        source_market_id="12", source_market_name="Azadpur"))
    source_session.add(SourceMarketMapping(
        market_id=m2.id, source_code="ENAM",
        source_market_id="77", source_market_name="Azadpur"))
    await source_session.flush()
    rows = (await source_session.execute(select(SourceMarketMapping))).scalars().all()
    assert {(r.source_code, r.source_market_id) for r in rows} == {
        ("AGMARKNET", "12"), ("ENAM", "77")}


async def test_commodity_mapping_defaults_unmapped(source_session):
    from models.market_sources import CommodityMaster, SourceCommodityMapping

    c = CommodityMaster(display_name="Tomato")
    source_session.add(c)
    await source_session.flush()
    source_session.add(SourceCommodityMapping(
        commodity_id=c.id, source_code="DCA_PMD",
        source_commodity_name="Tomato Centre A"))
    await source_session.flush()
    row = (await source_session.execute(select(SourceCommodityMapping))).scalars().one()
    assert row.status == "unmapped"


async def test_distinct_observation_tables_hold_semantics(source_session):
    from datetime import date

    from models.market_sources import ConsumerPrice, ExchangeObservation, TradeStat

    source_session.add(ConsumerPrice(
        source_code="DCA_PMD", centre="Delhi", commodity="Onion",
        price_type="retail", price=40.0, unit="Rs/Kg",
        observation_date=date(2026, 9, 21)))
    source_session.add(TradeStat(
        source_code="TRADESTAT", commodity="Onion", hs_code="070310",
        country="UAE", trade_type="export", month=date(2026, 8, 1),
        quantity=1000.0, quantity_unit="MT", value=2.5, value_unit="USD Million"))
    source_session.add(ExchangeObservation(
        source_code="MCX", instrument="FUTCOM", commodity="Cardamom",
        open=3400.0, high=3450.0, low=3390.0, close=3447.0,
        observation_date=date(2026, 9, 21)))
    await source_session.flush()
    assert (await source_session.execute(select(ConsumerPrice))).scalars().one().price == 40.0
    assert (await source_session.execute(select(TradeStat))).scalars().one().hs_code == "070310"
    assert (await source_session.execute(select(ExchangeObservation))).scalars().one().close == 3447.0


async def test_sources_endpoint_registered():
    from api.v1.router import v1_router

    paths = [getattr(r, "path", "") for r in v1_router.routes]
    assert "/api/v1/market-data/sources" in paths


def _arrival_record(**overrides):
    record = {
        "state": "Telangana", "district": "Ranga Reddy", "market": "TestMandi",
        "commodity": "Tomato", "variety": "Local", "grade": "FAQ",
        "min_price": "1000", "max_price": "1500", "modal_price": "1200",
        "unit": "Rs/Quintal", "arrival_date": "21/09/2026",
    }
    record.update(overrides)
    return record


def test_normalize_record_keeps_valid_arrivals():
    from services.market_normalization import normalize_record

    obs, reason = normalize_record(
        _arrival_record(arrivals="48.5", unitOfArrivals="Tonnes"))
    assert reason is None
    assert obs is not None
    assert obs.arrivals is not None
    assert float(obs.arrivals) == 48.5
    assert obs.arrival_unit == "Tonnes"


def test_normalize_record_malformed_arrivals_never_zeroes_price():
    from services.market_normalization import normalize_record

    obs, reason = normalize_record(_arrival_record(arrivals="N/A"))
    assert reason is None
    assert obs is not None
    assert obs.arrivals is None
    assert float(obs.modal_price) == 1200


def test_normalize_record_arrivals_outside_natural_key():
    from services.market_normalization import normalize_record

    first, _ = normalize_record(_arrival_record(arrivals="10"))
    second, _ = normalize_record(_arrival_record(arrivals="99"))
    assert first is not None and second is not None
    assert first.natural_key() == second.natural_key()


async def test_ingest_source_rejects_unknown_source():
    from workers.tasks import _ingest_source

    with pytest.raises(ValueError, match="No ingestion implementation registered"):
        await _ingest_source("DCA_PMD")
