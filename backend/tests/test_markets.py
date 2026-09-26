"""Market Intelligence tests: normalization, OGD client, repository, service, API.

Uses mocked OGD responses/fixtures. No real API key required.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.market_normalization import (
    normalize_record,
    normalize_unit,
    parse_arrival_date,
    parse_price,
)


# ---------- normalization ----------


def _raw(**overrides):
    record = {
        "state": "Telangana",
        "district": " Medchal-Malkajgiri ",
        "market": "Bowenpally",
        "commodity": "Tomato",
        "variety": "Hybrid",
        "grade": "FAQ",
        "arrival_date": "2026-09-18",
        "min_price": "1,200",
        "max_price": 1800,
        "modal_price": "1500",
    }
    record.update(overrides)
    return record


def test_normalize_valid_record():
    obs, reason = normalize_record(_raw())
    assert reason is None
    assert obs is not None
    assert obs.district == "Medchal-Malkajgiri"
    assert obs.min_price == Decimal("1200")
    assert obs.modal_price == Decimal("1500")
    assert obs.price_per_unit == "INR/quintal"
    assert obs.arrival_date == date(2026, 9, 18)
    assert len(obs.natural_key()) == 7


def test_normalize_rejects_missing_dimensions():
    obs, reason = normalize_record(_raw(market="  "))
    assert obs is None and reason is not None


def test_normalize_rejects_bad_prices():
    for bad in ["NA", "", "abc", "-5", None, "Infinity", "-Infinity", "nan"]:
        obs, reason = normalize_record(_raw(modal_price=bad))
        assert obs is None, bad


def test_normalize_accepts_zero_prices():
    # Zero is a valid source value and must not be treated as missing.
    obs, reason = normalize_record(
        _raw(min_price="0", modal_price="0", max_price="0")
    )
    assert reason is None
    assert obs is not None
    assert obs.modal_price == Decimal("0")


def test_normalize_rejects_future_arrival_date():
    future = (date.today() + timedelta(days=30)).isoformat()
    obs, reason = normalize_record(_raw(arrival_date=future))
    assert obs is None
    assert reason is not None and "future" in reason


def test_normalize_rejects_ordering_violation():
    obs, reason = normalize_record(_raw(min_price="2000", modal_price="1500"))
    assert obs is None
    assert reason is not None and "ordering" in reason


def test_normalize_rejects_incompatible_unit():
    obs, reason = normalize_record(_raw(unit="Rs/Kg"))
    assert obs is None


def test_normalize_unit_variants():
    assert normalize_unit("Rs/Quintal") == "INR/quintal"
    assert normalize_unit("INR/quintal") == "INR/quintal"
    assert normalize_unit("Rs/Kg") is None


def test_parse_price_decimal():
    assert parse_price("1,200.50") == Decimal("1200.50")
    assert isinstance(parse_price("100"), Decimal)


def test_parse_arrival_date_formats():
    assert parse_arrival_date("2026-09-18") == date(2026, 9, 18)
    assert parse_arrival_date("18/09/2026") == date(2026, 9, 18)
    assert parse_arrival_date("not-a-date") is None


# ---------- OGD client ----------


async def test_ogd_client_requires_key(monkeypatch):
    from services import ogd_client

    monkeypatch.setattr(ogd_client.settings, "DATA_GOV_API_KEY", "")
    with pytest.raises(ogd_client.OgdConfigError):
        await ogd_client.fetch_mandi_records(state="Telangana")


async def test_ogd_client_pagination_and_filters(monkeypatch):
    from services import ogd_client

    seen_queries = []

    page1 = {
        "total": 3,
        "count": 2,
        "records": [
            {"state": "Telangana", "commodity": "Tomato"},
            {"state": "Telangana", "commodity": "Tomato"},
        ],
    }
    page2 = {"total": 3, "count": 1, "records": [{"state": "Telangana"}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, params=None):
            assert params is not None
            seen_queries.append(params)
            if params["offset"] == 0:
                return Response(200, json=page1)
            return Response(200, json=page2)

    monkeypatch.setattr(ogd_client, "AsyncClient", FakeClient)
    records, truncated = await ogd_client.fetch_mandi_records(
        state="Telangana",
        commodity="Tomato",
        limit_total=10,
        api_key="test-key",
        page_size=2,
    )
    assert len(records) == 3
    assert truncated is False
    assert seen_queries[0]["filters[state.keyword]"] == "Telangana"
    assert seen_queries[0]["filters[commodity]"] == "Tomato"
    assert seen_queries[1]["offset"] == 2


async def test_ogd_client_truncation_flag(monkeypatch):
    from services import ogd_client

    class FullPages:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, params=None):
            assert params is not None
            # Endless full pages; the source total exceeds our safety bound.
            n = params["limit"]
            return Response(
                200,
                json={
                    "total": 100,
                    "records": [{"state": "X"} for _ in range(n)],
                },
            )

    monkeypatch.setattr(ogd_client, "AsyncClient", FullPages)
    records, truncated = await ogd_client.fetch_mandi_records(
        limit_total=5, api_key="test-key", page_size=2
    )
    assert len(records) == 5
    assert truncated is True


async def test_ogd_client_string_total(monkeypatch):
    from services import ogd_client

    class StringTotal:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, params=None):
            assert params is not None
            if params["offset"] == 0:
                return Response(
                    200, json={"total": "1", "records": [{"state": "X"}]}
                )
            return Response(200, json={"total": "1", "records": []})

    monkeypatch.setattr(ogd_client, "AsyncClient", StringTotal)
    records, truncated = await ogd_client.fetch_mandi_records(
        limit_total=10, api_key="test-key", page_size=5
    )
    assert len(records) == 1
    assert truncated is False


async def test_ogd_client_upstream_error(monkeypatch):
    from services import ogd_client

    class BadClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, params=None):
            return Response(500, json={})

    monkeypatch.setattr(ogd_client, "AsyncClient", BadClient)
    with pytest.raises(ogd_client.OgdUpstreamError):
        await ogd_client.fetch_mandi_records(state="Telangana", api_key="k")


# ---------- repository / service (sqlite, market tables only) ----------


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
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


def _obs_payload(
    market="Bowenpally",
    arrival=None,
    modal: int | str = 1500,
    variety="Hybrid",
    state="Telangana",
    district="Medchal-Malkajgiri",
    commodity="Tomato",
    grade="FAQ",
):
    day = arrival or (date.today() - timedelta(days=1))
    modal_int = int(modal) if str(modal).lstrip("-").isdigit() else 1500
    return {
        "state": state,
        "district": district,
        "market": market,
        "commodity": commodity,
        "variety": variety,
        "grade": grade,
        "arrival_date": day.isoformat(),
        "min_price": str(modal_int - 300),
        "max_price": str(modal_int + 300),
        "modal_price": str(modal),
    }


async def test_store_observation_idempotent(market_session: AsyncSession):
    from repositories.market import market_repository

    raw = _obs_payload()
    row1, created1 = await market_repository.store_observation(
        market_session,
        state=raw["state"],
        district=raw["district"],
        market=raw["market"],
        commodity=raw["commodity"],
        variety=raw["variety"],
        grade=raw["grade"],
        arrival=date.fromisoformat(raw["arrival_date"]),
        min_price=1200,
        max_price=1800,
        modal_price=1500,
        price_per_unit="INR/quintal",
        raw_record=raw,
    )
    row2, created2 = await market_repository.store_observation(
        market_session,
        state=raw["state"],
        district=raw["district"],
        market=raw["market"],
        commodity=raw["commodity"],
        variety=raw["variety"],
        grade=raw["grade"],
        arrival=date.fromisoformat(raw["arrival_date"]),
        min_price=1200,
        max_price=1800,
        modal_price=1500,
        price_per_unit="INR/quintal",
        raw_record=raw,
    )
    assert created1 is True
    assert created2 is False
    assert row1.id == row2.id


async def test_get_latest_per_group(market_session: AsyncSession):
    from repositories.market import market_repository

    today = date.today()
    for market, day_offset in [
        ("Bowenpally", 1),
        ("Bowenpally", 5),
        ("Gudimalkapur", 2),
    ]:
        await market_repository.store_observation(
            market_session,
            state="Telangana",
            district="Hyderabad",
            market=market,
            commodity="Tomato",
            variety="Hybrid",
            grade="FAQ",
            arrival=today - timedelta(days=day_offset),
            min_price=1000,
            max_price=1600,
            modal_price=1300,
            price_per_unit="INR/quintal",
        )
    rows = await market_repository.get_latest(market_session, state="Telangana")
    assert len(rows) == 2
    by_market = {r.market: r.arrival_date for r in rows}
    assert by_market["Bowenpally"] == today - timedelta(days=1)
    assert by_market["Gudimalkapur"] == today - timedelta(days=2)


async def test_ingest_records_counts_and_skips(market_session: AsyncSession):
    from services.market import market_service

    raws = [_obs_payload(), _obs_payload(), _obs_payload(modal="bad")]
    stored, skipped, min_seen, max_seen = await market_service.ingest_records(
        market_session, raws
    )
    assert stored == 1
    assert skipped == 2  # one duplicate, one malformed
    assert min_seen == max_seen


async def test_telangana_latest_envelope(market_session: AsyncSession):
    from services.market import market_service

    await market_service.ingest_records(market_session, [_obs_payload()])
    resp = await market_service.get_telangana_latest(market_session)
    assert len(resp.items) == 1
    assert resp.provenance.resource_id
    assert resp.freshness.latest_observation_date is not None
    assert resp.freshness.is_stale is False


async def test_telangana_history_lineage_and_stats(market_session: AsyncSession):
    from services.market import market_service

    today = date.today()
    raws = []
    for i in range(5):
        day = today - timedelta(days=i + 1)
        raws.append(_obs_payload(arrival=day, modal=1500 + i * 10))
    # A second variety must not pollute the series.
    raws.append(_obs_payload(arrival=today - timedelta(days=1), variety="Desi"))
    await market_service.ingest_records(market_session, raws)
    resp = await market_service.get_telangana_history(
        market_session, commodity="Tomato", market="Bowenpally", days=30
    )
    assert resp.stats.point_count == 5
    assert resp.stats.last_modal_price != resp.stats.first_modal_price
    assert all(p.market == "Bowenpally" for p in resp.points)
    assert resp.points == sorted(resp.points, key=lambda p: p.arrival_date)


async def test_telangana_history_empty(market_session: AsyncSession):
    from services.market import market_service

    resp = await market_service.get_telangana_history(
        market_session, commodity="NoSuchCrop", days=7
    )
    assert resp.points == []
    assert resp.stats.point_count == 0


async def test_telangana_comparison_orders_by_modal(market_session: AsyncSession):
    from services.market import market_service

    await market_service.ingest_records(
        market_session,
        [_obs_payload(market="Bowenpally", modal=1500), _obs_payload(market="Zahirabad", modal=1700)],
    )
    resp = await market_service.get_telangana_comparison(
        market_session, commodity="Tomato"
    )
    assert [r.market for r in resp.rows] == ["Bowenpally", "Zahirabad"]
    assert "matching variety" in resp.group["note"]


# ---------- API ----------


@pytest_asyncio.fixture
async def api_client(market_session):
    from core.dependencies import get_current_user, get_db
    from main import app
    from models.user import User

    async def override_db():
        yield market_session

    async def override_user():
        return User(
            email="farmer@test.in",
            password_hash="x",
            full_name="Test Farmer",
            role="farmer",
            state="Telangana",
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


async def test_api_requires_auth(market_session, monkeypatch):
    from core.config import settings
    from core.dependencies import get_db
    from main import app

    # Production behavior must hold regardless of local .env contents.
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "DEV_AUTH_BYPASS", True)

    async def override_db():
        yield market_session

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/markets/telangana/latest")
    app.dependency_overrides.clear()
    assert resp.status_code in (401, 403)


async def test_api_latest_empty(api_client: AsyncClient):
    resp = await api_client.get("/api/v1/markets/telangana/latest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["provenance"]["name"] == "AGMARKNET"
    assert body["freshness"]["observation_count"] == 0


async def test_api_latest_and_meta(api_client: AsyncClient, market_session):
    from services.market import market_service

    await market_service.ingest_records(market_session, [_obs_payload()])
    resp = await api_client.get(
        "/api/v1/markets/telangana/latest", params={"commodity": "Tomato"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["arrival_date"]
    assert item["source"] == "AGMARKNET"

    meta = await api_client.get("/api/v1/markets/telangana/meta/districts")
    assert meta.status_code == 200
    assert "Medchal-Malkajgiri" in meta.json()["values"]


async def test_api_history_and_comparison(api_client: AsyncClient, market_session):
    from services.market import market_service

    today = date.today()
    await market_service.ingest_records(
        market_session,
        [
            _obs_payload(arrival=today - timedelta(days=1), modal=1500),
            _obs_payload(arrival=today - timedelta(days=2), modal=1400),
            _obs_payload(
                market="Zahirabad",
                arrival=today - timedelta(days=1),
                modal=1700,
            ),
        ],
    )
    hist = await api_client.get(
        "/api/v1/markets/telangana/history",
        params={"commodity": "Tomato", "market": "Bowenpally", "days": 30},
    )
    assert hist.status_code == 200
    assert hist.json()["stats"]["point_count"] == 2

    comp = await api_client.get(
        "/api/v1/markets/telangana/comparison", params={"commodity": "Tomato"}
    )
    assert comp.status_code == 200
    assert len(comp.json()["rows"]) == 2


# ---------- national behavior ----------


async def test_national_latest_does_not_collapse_markets(
    market_session: AsyncSession,
):
    from services.market import market_service

    await market_service.ingest_records(
        market_session,
        [
            _obs_payload(market="Market A", district="D1", modal=1500),
            _obs_payload(market="Market B", district="D2", modal=1600),
            _obs_payload(
                market="Market C",
                state="Karnataka",
                district="D3",
                modal=1700,
            ),
        ],
    )
    resp = await market_service.get_latest(market_session, commodity="Tomato")
    assert len(resp.items) == 3

    filtered = await market_service.get_latest(
        market_session, commodity="Tomato", state="Telangana"
    )
    assert len(filtered.items) == 2

    district = await market_service.get_latest(
        market_session, commodity="Tomato", state="Telangana", district="D1"
    )
    assert len(district.items) == 1
    assert district.items[0].market == "Market A"


async def test_ingest_duplicate_same_key_stores_once(
    market_session: AsyncSession,
):
    from repositories.market import market_repository
    from services.market import market_service

    raw = _obs_payload()
    stored, skipped, _, _ = await market_service.ingest_records(
        market_session, [raw, dict(raw)]
    )
    assert stored == 1
    assert skipped == 1
    count = await market_repository.count(market_session)
    assert count == 1


async def test_grades_stay_separate(market_session: AsyncSession):
    from services.market import market_service

    await market_service.ingest_records(
        market_session,
        [_obs_payload(grade="FAQ"), _obs_payload(grade="Super")],
    )
    resp = await market_service.get_latest(market_session, commodity="Tomato")
    assert len(resp.items) == 2
    assert {i.grade for i in resp.items} == {"FAQ", "Super"}


async def test_same_market_name_across_districts_stays_separate(
    market_session: AsyncSession,
):
    from services.market import market_service

    await market_service.ingest_records(
        market_session,
        [
            _obs_payload(market="Main Market", district="D1", modal=1500),
            _obs_payload(market="Main Market", district="D2", modal=1600),
        ],
    )
    resp = await market_service.get_latest(market_session, commodity="Tomato")
    assert len(resp.items) == 2
    assert {i.district for i in resp.items} == {"D1", "D2"}


async def test_legacy_null_row_does_not_duplicate_on_reingest(
    market_session: AsyncSession,
):
    from datetime import date as date_cls

    from models.market import MarketPrice
    from repositories.market import market_repository
    from services.market import market_service

    # Simulate a pre-backfill legacy row with NULL dimensions.
    market_session.add(
        MarketPrice(
            state="Telangana",
            district=None,
            market="Old Market",
            commodity="Tomato",
            variety=None,
            grade=None,
            arrival_date=date_cls.today(),
            min_price=1000,
            max_price=1600,
            modal_price=1300,
            price_per_unit="INR/quintal",
            source="AGMARKNET",
        )
    )
    await market_session.flush()
    stored, skipped, _, _ = await market_service.ingest_records(
        market_session,
        [
            _obs_payload(
                market="Old Market",
                district="",
                variety="",
                grade="",
                arrival=date_cls.today(),
                modal=1300,
            )
        ],
    )
    assert stored == 0
    assert skipped == 1
    assert await market_repository.count(market_session) == 1


async def test_meta_states_districts_varieties_grades(
    market_session: AsyncSession,
):
    from services.market import market_service

    await market_service.ingest_records(
        market_session,
        [
            _obs_payload(variety="Hybrid", grade="FAQ"),
            _obs_payload(
                market="Market C",
                state="Karnataka",
                district="Mandi",
                variety="Desi",
                grade="Super",
            ),
        ],
    )
    states = await market_service.get_states(market_session)
    assert set(states.values) == {"Karnataka", "Telangana"}

    districts_all = await market_service.get_districts(market_session)
    assert set(districts_all.values) == {"Mandi", "Medchal-Malkajgiri"}

    districts_tg = await market_service.get_districts(
        market_session, state="Telangana"
    )
    assert districts_tg.values == ["Medchal-Malkajgiri"]

    varieties = await market_service.get_varieties(
        market_session, state="Karnataka"
    )
    assert varieties.values == ["Desi"]

    grades = await market_service.get_grades(
        market_session, commodity="Tomato", variety="Hybrid"
    )
    assert grades.values == ["FAQ"]


async def test_latest_pagination(market_session: AsyncSession):
    from services.market import market_service

    await market_service.ingest_records(
        market_session,
        [_obs_payload(market=f"M{i}", modal=1000 + i) for i in range(5)],
    )
    page1 = await market_service.get_latest(
        market_session, commodity="Tomato", limit=2, offset=0
    )
    page2 = await market_service.get_latest(
        market_session, commodity="Tomato", limit=2, offset=2
    )
    assert len(page1.items) == 2
    assert len(page2.items) == 2
    ids1 = {i.id for i in page1.items}
    ids2 = {i.id for i in page2.items}
    assert not ids1 & ids2


async def test_history_date_range(market_session: AsyncSession):
    from services.market import market_service

    today = date.today()
    await market_service.ingest_records(
        market_session,
        [
            _obs_payload(arrival=today - timedelta(days=1)),
            _obs_payload(arrival=today - timedelta(days=10)),
            _obs_payload(arrival=today - timedelta(days=40)),
        ],
    )
    ranged = await market_service.get_history(
        market_session,
        commodity="Tomato",
        market="Bowenpally",
        from_date=today - timedelta(days=15),
        to_date=today,
    )
    assert ranged.stats.point_count == 2

    windowed = await market_service.get_history(
        market_session, commodity="Tomato", market="Bowenpally", days=7
    )
    assert windowed.stats.point_count == 1


async def test_ingest_date_range_skips(market_session: AsyncSession):
    from services.market import market_service

    today = date.today()
    stored, skipped, _, _ = await market_service.ingest_records(
        market_session,
        [_obs_payload(arrival=today - timedelta(days=30))],
        start_date=today - timedelta(days=7),
    )
    assert stored == 0
    assert skipped == 1


async def test_overview_counts(market_session: AsyncSession):
    from services.market import market_service

    await market_service.ingest_records(
        market_session,
        [
            _obs_payload(),
            _obs_payload(market="Market C", state="Karnataka", district="Mandi"),
        ],
    )
    national = await market_service.get_overview(market_session)
    assert national.states_reporting == 2
    assert national.markets_reporting == 2
    assert national.commodities_reported == 1
    assert national.latest_observation_date is not None

    scoped = await market_service.get_overview(market_session, state="Karnataka")
    assert scoped.states_reporting == 1
    assert scoped.markets_reporting == 1


async def test_stale_flagged_when_old(market_session: AsyncSession):
    from services.market import market_service

    await market_service.ingest_records(
        market_session,
        [_obs_payload(arrival=date.today() - timedelta(days=10))],
    )
    resp = await market_service.get_latest(market_session)
    assert resp.freshness.is_stale is True
    assert resp.freshness.age_days == 10


async def test_api_neutral_endpoints(api_client: AsyncClient, market_session):
    from services.market import market_service

    today = date.today()
    await market_service.ingest_records(
        market_session,
        [
            _obs_payload(arrival=today - timedelta(days=1), modal=1500),
            _obs_payload(
                market="Market C",
                state="Karnataka",
                district="Mandi",
                arrival=today - timedelta(days=1),
                modal=1700,
            ),
        ],
    )
    latest = await api_client.get(
        "/api/v1/markets/latest", params={"commodity": "Tomato"}
    )
    assert latest.status_code == 200
    assert len(latest.json()["items"]) == 2
    assert {i["state"] for i in latest.json()["items"]} == {
        "Karnataka",
        "Telangana",
    }

    states = await api_client.get("/api/v1/markets/meta/states")
    assert states.status_code == 200
    assert set(states.json()["values"]) == {"Karnataka", "Telangana"}

    varieties = await api_client.get(
        "/api/v1/markets/meta/varieties", params={"commodity": "Tomato"}
    )
    assert varieties.status_code == 200
    assert varieties.json()["values"] == ["Hybrid"]

    overview = await api_client.get("/api/v1/markets/overview")
    assert overview.status_code == 200
    assert overview.json()["states_reporting"] == 2

    hist = await api_client.get(
        "/api/v1/markets/history",
        params={"commodity": "Tomato", "state": "Telangana", "days": 30},
    )
    assert hist.status_code == 200
    assert hist.json()["stats"]["point_count"] == 1

    comp = await api_client.get(
        "/api/v1/markets/comparison", params={"commodity": "Tomato"}
    )
    assert comp.status_code == 200
    rows = comp.json()["rows"]
    assert len(rows) == 2
    assert all("state" in r for r in rows)
