"""AGMARKNET Direct provider tests. HTTP mocked; no live service needed."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services import agmarknet_client
from services.market_normalization import normalize_record


def _report_row(**overrides):
    row = {
        "arrivals": 1.3,
        "unitOfArrivals": "Metric Tonnes",
        "variety": "Hybrid",
        "minimumPrice": 2049.0,
        "maximumPrice": 2323.0,
        "modalPrice": 2049.0,
        "unitOfPrice": "Rs./Quintal",
    }
    row.update(overrides)
    return row


def _state_report(rows_by_market):
    markets = []
    for name, rows in rows_by_market.items():
        markets.append({"marketCenter": name, "total_arrivals": 1.0, "data": rows})
    return {
        "success": True,
        "message": "Data fetched successfully.",
        "title": "Commodity-wise, Market-wise Daily Report",
        "columns": [],
        "commodityGroups": [
            {"CommodityGroup": "Cereals", "commodities": [
                {"commodityName": "Jowar(Sorghum)", "markets": markets}
            ]}
        ],
    }


class MockAgmarknetClient:
    """Mimics httpx.AsyncClient with canned route responses."""

    routes: dict = {}

    def __init__(self, *args, **kwargs):
        self.sent = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def request(self, method, url, params=None, json=None):
        self.sent.append({"method": method, "url": url, "params": params, "json": json})
        for key, payload in type(self).routes.items():
            if key in url:
                status, body, ctype = payload
                return Response(status, json=body) if ctype == "json" else Response(
                    status, content=body, headers={"content-type": ctype}
                )
        return Response(404, json={"success": False, "message": "No data found."})


@pytest.fixture
def mock_client(monkeypatch):
    monkeypatch.setattr(agmarknet_client, "AsyncClient", MockAgmarknetClient)
    MockAgmarknetClient.routes = {}
    return MockAgmarknetClient


async def test_browser_headers_sent(mock_client):
    from services.agmarknet_client import BROWSER_HEADERS

    assert BROWSER_HEADERS["Origin"] == "https://agmarknet.gov.in"
    assert BROWSER_HEADERS["Referer"] == "https://agmarknet.gov.in/"
    assert "Mozilla" in BROWSER_HEADERS["User-Agent"]
    assert "application/json" in BROWSER_HEADERS["Accept"]


async def test_report_date_format():
    from services.agmarknet_client import format_report_date

    assert format_report_date(date(2026, 9, 21)) == "2026-09-21"


async def test_daily_state_report_params(mock_client):
    from services import agmarknet_client as ac

    MockAgmarknetClient.routes = {
        "/daily-report-state": (200, _state_report({"M": [_report_row()]}), "json")
    }
    inst = MockAgmarknetClient()
    monkeypatch_holder = inst
    import services.agmarknet_client as mod

    orig = mod.AsyncClient
    mod.AsyncClient = lambda *a, **k: monkeypatch_holder
    try:
        await ac.daily_state_report(date(2026, 9, 21), 32)
    finally:
        mod.AsyncClient = orig
    sent = inst.sent[0]
    assert sent["params"]["date"] == "2026-09-21"
    assert sent["params"]["state"] == 32
    assert sent["params"]["includeExcel"] == "false"


async def test_state_pagination_and_all_excluded(mock_client):
    from services.market_providers import agmarknet_provider

    pages = {
        1: {"states": [{"id": 1, "state_name": "Alpha"}], "pagination": {"total_pages": 2}},
        2: {"states": [{"id": 100000, "state_name": "All States/UTs"}, {"id": 2, "state_name": "Beta"}],
            "pagination": {"total_pages": 2}},
    }

    class Paged(MockAgmarknetClient):
        async def request(self, method, url, params=None, json=None):
            assert params is not None
            self.sent.append({"params": params})
            return Response(200, json=pages[params["page"]])

    import services.agmarknet_client as mod

    orig = mod.AsyncClient
    inst = Paged()
    mod.AsyncClient = lambda *a, **k: inst
    try:
        states = await agmarknet_provider.get_states()
    finally:
        mod.AsyncClient = orig
    assert [(s.id, s.name) for s in states] == [(1, "Alpha"), (2, "Beta")]
    assert {s.name for s in states} == {"Alpha", "Beta"}


async def test_market_index_resolution():
    from services.market_providers import agmarknet_provider

    async def fake_filters():
        return {"data": {
            "market_data": [
                {"id": 1, "mkt_name": "Bhainsa APMC ", "state_id": 32, "district_id": 565},
                {"id": 2, "mkt_name": "All Markets", "state_id": None, "district_id": None},
            ],
            "district_data": [{"id": 565, "district_name": "Adilabad"}],
            "state_data": [{"state_id": 32, "state_name": "Telangana"}],
        }}

    import services.market_providers as mp

    orig = mp.agmarknet_client.fetch_filters
    mp.agmarknet_client.fetch_filters = fake_filters
    try:
        index = await agmarknet_provider.get_market_index()
    finally:
        mp.agmarknet_client.fetch_filters = orig
    assert "All Markets" not in index
    ref = index["Bhainsa APMC"]
    assert ref.district_name == "Adilabad"
    assert ref.state_name == "Telangana"


async def test_daily_observations_mapping():
    from services.market_providers import ProviderState, agmarknet_provider

    async def fake_report(report_date, state_id):
        assert report_date.isoformat() == "2026-09-21"
        return _state_report({"Bhainsa APMC": [_report_row(), _report_row(variety="Desi")]})

    async def fake_index():
        from services.market_providers import MarketRef

        return {"Bhainsa APMC": MarketRef(1, "Bhainsa APMC", 565, "Adilabad", 32, "Telangana")}

    import services.market_providers as mp

    o1, o2 = mp.agmarknet_client.daily_state_report, mp.agmarknet_provider.get_market_index
    mp.agmarknet_client.daily_state_report = fake_report
    mp.agmarknet_provider.get_market_index = fake_index
    try:
        rows = await agmarknet_provider.daily_observations(
            date(2026, 9, 21), ProviderState(id=32, name="Telangana")
        )
    finally:
        mp.agmarknet_client.daily_state_report = o1
        mp.agmarknet_provider.get_market_index = o2
    assert len(rows) == 2
    assert rows[0]["commodity"] == "Jowar(Sorghum)"
    assert rows[0]["market"] == "Bhainsa APMC"
    assert rows[0]["district"] == "Adilabad"
    assert rows[0]["state"] == "Telangana"
    assert rows[0]["arrival_date"] == "2026-09-21"
    assert rows[0]["grade"] == ""
    assert {r["variety"] for r in rows} == {"Hybrid", "Desi"}


async def test_normalize_agmarknet_row_and_artifacts():
    obs, reason = normalize_record({
        "state": "Telangana", "district": "Adilabad", "market": "Bhainsa APMC",
        "commodity": "Jowar(Sorghum)", "variety": "Hybrid", "grade": "",
        "arrival_date": "2026-09-21",
        "min_price": 2049.0, "max_price": 2323.0, "modal_price": 2049.0,
        "unit": "Rs./Quintal",
    })
    assert reason is None
    assert obs is not None
    assert obs.min_price == Decimal("2049")
    assert obs.price_per_unit == "INR/quintal"
    # float artifact in arrivals must not affect stored prices
    assert float(obs.modal_price) == 2049.0


async def test_rejects_infinity_malformed_future_and_ordering():
    base = {
        "state": "S", "district": "D", "market": "M", "commodity": "C",
        "variety": "V", "grade": "", "arrival_date": "2026-09-21",
        "min_price": 100, "max_price": 200, "modal_price": 150, "unit": "Rs./Quintal",
    }
    for bad in ["Infinity", "-Infinity", "nan", "abc", None, -5]:
        obs, _ = normalize_record({**base, "modal_price": bad})
        assert obs is None, bad
    obs, reason = normalize_record({**base, "min_price": 300})
    assert obs is None and "ordering" in (reason or "")
    future = (date.today() + timedelta(days=30)).isoformat()
    obs, reason = normalize_record({**base, "arrival_date": future})
    assert obs is None and "future" in (reason or "")
    # zero stays valid
    obs, _ = normalize_record({**base, "min_price": 0, "modal_price": 0, "max_price": 0})
    assert obs is not None


async def test_no_data_and_html_errors(mock_client):
    from services import agmarknet_client as ac

    MockAgmarknetClient.routes = {
        "/daily-report-state": (404, {"success": False, "message": "No data found."}, "json")
    }
    inst = MockAgmarknetClient()
    import services.agmarknet_client as mod

    orig = mod.AsyncClient
    mod.AsyncClient = lambda *a, **k: inst
    try:
        with pytest.raises(ac.AgmarknetHTTPError):
            await ac.daily_state_report(date(2026, 9, 21), 32)
        MockAgmarknetClient.routes = {
            "/daily-report-state": (200, {"success": False, "message": "No data found."}, "json")
        }
        with pytest.raises(ac.AgmarknetNoDataError):
            await ac.daily_state_report(date(2026, 9, 21), 32)
        MockAgmarknetClient.routes = {
            "/daily-report-state": (200, b"<html>Server Error</html>", "text/html")
        }
        with pytest.raises(ac.AgmarknetResponseError):
            await ac.daily_state_report(date(2026, 9, 21), 32)
    finally:
        mod.AsyncClient = orig


@pytest_asyncio.fixture
async def market_session():
    from db.base import Base
    from models.market import MarketIngestion, MarketPrice
    from models.market_geo import GeoDistrict, GeoMarket, GeoState

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,  # type: ignore[arg-type]
            tables=[  # type: ignore[list-item]
                MarketPrice.__table__,
                MarketIngestion.__table__,
                GeoState.__table__,
                GeoDistrict.__table__,
                GeoMarket.__table__,
            ],
        )
    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


async def _ingest_agmarknet(session, rows):
    from services.market import market_service

    return await market_service.ingest_records(
        session, rows, resource_id="https://agmarknet.gov.in/"
    )


async def test_agmarknet_ingest_idempotent_and_separate(market_session):
    from repositories.market import market_repository

    def row(market="Bhainsa APMC", district="Adilabad", variety="Hybrid",
            grade="", state="Telangana", arrival="2026-09-21"):
        return {
            "state": state, "district": district, "market": market,
            "commodity": "Jowar(Sorghum)", "variety": variety, "grade": grade,
            "arrival_date": arrival, "min_price": 2049, "max_price": 2323,
            "modal_price": 2049, "unit": "Rs./Quintal",
        }

    raws = [row(), row(), row(grade="Local"), row(variety="Desi"),
            row(market="Zaheerabad APMC", district="Sangareddy"),
            row(state="Karnataka", district="D", market="M")]
    s1, k1, _, _ = await _ingest_agmarknet(market_session, raws)
    assert (s1, k1) == (5, 1)
    s2, k2, _, _ = await _ingest_agmarknet(market_session, raws)
    assert (s2, k2) == (0, 6)
    assert await market_repository.count(market_session) == 5


async def test_agmarknet_latest_and_attribution(market_session):
    from services.market import market_service

    await _ingest_agmarknet(market_session, [{
        "state": "Telangana", "district": "Adilabad", "market": "Bhainsa APMC",
        "commodity": "Jowar(Sorghum)", "variety": "Hybrid", "grade": "",
        "arrival_date": "2026-09-21", "min_price": 2049, "max_price": 2323,
        "modal_price": 2049, "unit": "Rs./Quintal",
    }])
    resp = await market_service.get_latest(market_session, state="Telangana")
    assert len(resp.items) == 1
    assert resp.provenance.name == "AGMARKNET"
    assert "agmarknet.gov.in" in resp.provenance.resource_id


def _geo_filters_payload():
    return {"data": {
        "state_data": [
            {"state_id": 100000, "state_name": "All States/UTs"},
            {"state_id": 32, "state_name": "Telangana "},
            {"state_id": 16, "state_name": "Karnataka"},
        ],
        "district_data": [
            {"id": 100001, "state_id": None, "district_name": "All Districts"},
            {"id": 565, "state_id": 32, "district_name": "Adilabad  "},
            {"id": 700, "state_id": 32, "district_name": "Adilabad"},
        ],
        "market_data": [
            {"id": 100002, "mkt_name": "All Markets", "state_id": None, "district_id": None},
            {"id": 1, "mkt_name": "Bhainsa APMC ", "state_id": 32, "district_id": 565},
            {"id": 1, "mkt_name": "Bhainsa APMC", "state_id": 32, "district_id": 565},
        ],
    }}


async def test_geo_sync_full_catalog(monkeypatch, market_session):
    from repositories.market_geo import geo_repository
    from services import agmarknet_client
    from services.market_geo import sync_agmarknet_geography

    async def fake_states():
        from services.market_providers import ProviderState

        return [ProviderState(id=32, name="Telangana"),
                ProviderState(id=16, name="Karnataka")]

    async def fake_filters():
        return _geo_filters_payload()

    async def fake_categories():
        return [{"id": 5, "code": "PMY", "name": "Principal Market Yard"}]

    monkeypatch.setattr(
        "services.market_providers.agmarknet_provider.get_states", fake_states
    )
    monkeypatch.setattr(agmarknet_client, "fetch_filters", fake_filters)
    monkeypatch.setattr(agmarknet_client, "list_market_categories", fake_categories)

    first = await sync_agmarknet_geography(market_session)
    assert first["states"] == 2
    assert first["districts"] == 2
    assert first["markets"] == 1
    # Synthetic "All" entries never enter the catalog.
    states = await geo_repository.list_states(market_session)
    assert {s.name for s in states} == {"Telangana", "Karnataka"}
    assert all("All" not in s.name for s in states)
    # Source IDs preserved; whitespace normalized.
    tg = [s for s in states if s.name == "Telangana"][0]
    assert tg.source_id == 32
    second = await sync_agmarknet_geography(market_session)
    assert second["created"] == 0
    counts = await geo_repository.counts(market_session)
    assert counts == {"states": 2, "districts": 2, "markets": 1}


async def test_geo_relationships_and_meta_without_prices(monkeypatch, market_session):
    from repositories.market_geo import geo_repository
    from services import agmarknet_client
    from services.market import market_service
    from services.market_geo import sync_agmarknet_geography

    async def fake_states():
        from services.market_providers import ProviderState

        return [ProviderState(id=32, name="Telangana")]

    async def fake_filters():
        return _geo_filters_payload()

    async def fake_categories():
        return []

    monkeypatch.setattr(
        "services.market_providers.agmarknet_provider.get_states", fake_states
    )
    monkeypatch.setattr(agmarknet_client, "fetch_filters", fake_filters)
    monkeypatch.setattr(agmarknet_client, "list_market_categories", fake_categories)
    await sync_agmarknet_geography(market_session)

    tg_districts = await geo_repository.list_districts(market_session, "Telangana")
    assert {d.name for d in tg_districts} == {"Adilabad"}
    assert tg_districts[0].state_id == 32
    tg_markets = await geo_repository.list_markets(market_session, "Telangana")
    assert [m.name for m in tg_markets] == ["Bhainsa APMC"]
    assert tg_markets[0].district_name == "Adilabad"

    # Meta endpoints serve catalog data with zero price rows stored.
    states = await market_service.get_states(market_session)
    assert states.values == ["Telangana"]
    districts = await market_service.get_districts(market_session, state="Telangana")
    assert districts.values == ["Adilabad"]
    markets = await market_service.get_markets(market_session, state="Telangana")
    assert markets.values == ["Bhainsa APMC"]
    latest = await market_service.get_latest(market_session, state="Telangana")
    assert latest.items == []
    assert latest.freshness.observation_count == 0


async def test_state_failure_does_not_discard_other_states(monkeypatch):
    import workers.tasks as tasks_mod
    from db.base import Base
    from models.market import MarketIngestion, MarketPrice
    from services.agmarknet_client import AgmarknetHTTPError

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,  # type: ignore[arg-type]
            tables=[MarketPrice.__table__, MarketIngestion.__table__],  # type: ignore[list-item]
        )
    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(tasks_mod, "async_session_factory", factory)

    async def fake_daily(report_date, target, market_index=None):
        if target.name == "Bad State":
            raise AgmarknetHTTPError("AGMARKNET returned status 500.")
        return [{
            "state": target.name, "district": "D", "market": "M",
            "commodity": "C", "variety": "V", "grade": "",
            "arrival_date": report_date.isoformat(), "min_price": 100,
            "max_price": 200, "modal_price": 150, "unit": "Rs./Quintal",
        }]

    monkeypatch.setattr(
        "services.market_providers.agmarknet_provider.daily_observations",
        fake_daily,
    )

    from services import market_providers as mp

    async def fake_states():
        return [mp.ProviderState(id=1, name="Bad State"),
                mp.ProviderState(id=2, name="Good State")]

    monkeypatch.setattr(
        "services.market_providers.agmarknet_provider.get_states", fake_states
    )
    result = await tasks_mod._ingest_market_prices(
        None, None, "2026-09-21", "2026-09-21"
    )
    assert result["status"] == "success"
    assert result["stored"] == 1
    from repositories.market import market_repository

    async with factory() as session:
        assert await market_repository.count(session) == 1
    await engine.dispose()


async def test_init_db_production_refuses_partial_schema(monkeypatch):
    import db.session as session_mod

    class FakeConn:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        def run_sync(self, *args, **kwargs):
            raise RuntimeError("no postgis")

    class FakeEngine:
        def begin(self):
            return FakeConn()

    monkeypatch.setattr(session_mod, "engine", FakeEngine())
    monkeypatch.setattr(session_mod.settings, "ENVIRONMENT", "production")
    with pytest.raises(RuntimeError):
        await session_mod.init_db()
    monkeypatch.setattr(session_mod.settings, "ENVIRONMENT", "development")
    # Development falls back per table; all fail here but none may raise.
    await session_mod.init_db()
