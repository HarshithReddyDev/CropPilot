from datetime import datetime, timezone

import asyncio

from celery import shared_task
from sqlalchemy import text

from core.config import settings
from db.session import async_session_factory
from workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def process_vision_detection(self, disease_log_id: str):
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_process_detection(disease_log_id))
        loop.close()
        return {"status": "completed", "disease_log_id": disease_log_id}
    except Exception as e:
        raise self.retry(exc=e, countdown=60)


async def _process_detection(disease_log_id: str):
    async with async_session_factory() as session:
        from models.disease import DiseaseLog
        from sqlalchemy import select

        stmt = select(DiseaseLog).where(DiseaseLog.id == disease_log_id)
        result = await session.execute(stmt)
        log = result.scalar_one_or_none()
        if log and not log.severity or log.severity == "unknown":
            confidence = log.confidence or 0
            if confidence >= 0.8:
                log.severity = "high"
            elif confidence >= 0.5:
                log.severity = "medium"
            else:
                log.severity = "low"
            await session.flush()


@celery_app.task
def fetch_weather_data(h3_index: str, lat: float, lon: float):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_fetch_and_store_weather(h3_index, lat, lon))
    loop.close()
    return {"status": "completed", "h3_index": h3_index}


async def _fetch_and_store_weather(h3_index: str, lat: float, lon: float):
    from services.weather import weather_service
    async with async_session_factory() as session:
        await weather_service.fetch_and_store_weather(session, lat, lon, h3_index)


@celery_app.task
def cleanup_old_records():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_cleanup())
    loop.close()
    return {"status": "cleanup_completed"}


async def _cleanup():
    async with async_session_factory() as session:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        await session.execute(
            text("DELETE FROM analytics_events WHERE created_at < :cutoff"),
            {"cutoff": cutoff},
        )
        await session.execute(
            text("DELETE FROM weather_records WHERE created_at < :cutoff"),
            {"cutoff": cutoff},
        )
        await session.flush()


@celery_app.task(bind=True, max_retries=3)
def ingest_market_prices(
    self,
    state: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Ingest mandi observations from AGMARKNET Direct into stored views.

    State None means the national dataset (one daily report per
    discovered state). One reusable pipeline serves national runs and
    single-state debugging alike. Idempotent: repeated runs never
    duplicate observations (natural-key upsert). Failures are recorded
    on the ingestion audit row and retried. No API key required.
    """
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _ingest_market_prices(state, district, start_date, end_date)
        )
        loop.close()
        return result
    except Exception as e:
        raise self.retry(exc=e, countdown=300)


# Source-neutral orchestration: each provider keeps its own implementation
# internally; the dispatcher only routes by registered source code so one
# provider failure can never stop another provider.
SOURCE_INGESTORS = ("AGMARKNET",)


@celery_app.task(bind=True, max_retries=3)
def ingest_source(
    self,
    source_code: str,
    state: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Route ingestion to the provider registered for `source_code`."""
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _ingest_source(source_code, state, district, start_date, end_date)
        )
        loop.close()
        return result
    except Exception as e:
        raise self.retry(exc=e, countdown=300)


async def _ingest_source(
    source_code: str,
    state: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    code = (source_code or "").strip().upper()
    if code not in SOURCE_INGESTORS:
        raise ValueError(
            f"No ingestion implementation registered for source {source_code!r}. "
            f"Registered: {', '.join(SOURCE_INGESTORS)}."
        )
    return await _ingest_market_prices(state, district, start_date, end_date)


@celery_app.task(bind=True, max_retries=3)
def sync_market_geography(self):
    """Synchronize the AGMARKNET geography catalog (states/districts/markets).

    Independent of price ingestion: geography stays available even when
    price ingestion fails. Idempotent; safe to rerun.
    """
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_sync_market_geography())
        loop.close()
        return result
    except Exception as e:
        raise self.retry(exc=e, countdown=300)


async def _sync_market_geography():
    import structlog

    from services.agmarknet_client import AgmarknetError
    from services.market_geo import sync_agmarknet_geography

    logger = structlog.get_logger(__name__)
    async with async_session_factory() as session:
        try:
            result = await sync_agmarknet_geography(session)
            await session.commit()
        except AgmarknetError as e:
            await session.rollback()
            logger.warning("market_geo_sync_failed", error=str(e))
            return {"status": "failed", "error": str(e)}
        logger.info("market_geo_sync_task_completed", **result)
        return {"status": "success", **result}


@celery_app.task(bind=True, max_retries=3)
def ingest_telangana_market_prices(self, district: str | None = None):
    """Compatibility wrapper. Prefer ingest_market_prices(state=...)."""
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _ingest_market_prices("Telangana", district, None, None)
        )
        loop.close()
        return result
    except Exception as e:
        raise self.retry(exc=e, countdown=300)


async def _ingest_market_prices(
    state: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    import structlog
    from datetime import date as date_cls
    from datetime import timedelta

    from models.market import MarketIngestion
    from services.agmarknet_client import AgmarknetError
    from services.market import market_service
    from services.market_providers import (
        PROVIDER_NAME,
        SOURCE_URL,
        ProviderState,
        agmarknet_provider,
    )

    logger = structlog.get_logger(__name__)

    today = date_cls.today()
    start = date_cls.fromisoformat(start_date) if start_date else today
    end = date_cls.fromisoformat(end_date) if end_date else start
    if end < start:
        start, end = end, start
    dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    async with async_session_factory() as session:
        ingestion = MarketIngestion(
            resource_id=SOURCE_URL,
            provider=PROVIDER_NAME,
            state_filter=state or "national",
            status="running",
        )
        session.add(ingestion)
        await session.flush()
        await session.commit()

        if len(dates) > 8:
            ingestion.status = "failed"
            ingestion.error = (
                f"Date range too wide ({len(dates)} days, max 8 per run). "
                "Split the backfill into smaller windows."
            )
            ingestion.finished_at = datetime.now(timezone.utc)
            await session.flush()
            await session.commit()
            return {"status": "failed", "error": ingestion.error}

        try:
            if state:
                # Resolve the numeric source ID from the local catalog
                # first: no network call in the common case, and no
                # failure when the metadata endpoint is flaky.
                from repositories.market_geo import geo_repository

                catalog_row = await geo_repository.find_state(session, state)
                if catalog_row is not None and catalog_row.source_id is not None:
                    state_id: int | str = catalog_row.source_id
                    state_name = catalog_row.name
                else:
                    state_id = await agmarknet_provider.get_state_id(state)
                    if state_id is None:
                        raise AgmarknetError(f"Unknown state: {state!r}.")
                    state_name = state
                targets = [ProviderState(id=state_id, name=state_name)]
            else:
                targets = await agmarknet_provider.get_states()
            market_index = await agmarknet_provider.get_market_index()
        except AgmarknetError as e:
            logger.warning("market_ingest_upstream_failed", error=str(e))
            ingestion.status = "failed"
            ingestion.error = str(e)[:2000]
            ingestion.finished_at = datetime.now(timezone.utc)
            await session.flush()
            await session.commit()
            return {"status": "failed", "error": str(e)}

        fetched_total, stored_total, skipped_total = 0, 0, 0
        min_seen = None
        max_seen = None
        capped = False
        failed_parts: list[str] = []
        started_at = datetime.now(timezone.utc)

        # Phase 1: fetch concurrently with a small bound. Fetching is
        # stateless HTTP; the shared DB session is only touched in the
        # sequential store phase below (AsyncSession is not concurrency-safe).
        max_workers = max(1, settings.MARKET_INGEST_CONCURRENCY)
        semaphore = asyncio.Semaphore(max_workers)

        async def _fetch_one(report_date, target):
            async with semaphore:
                try:
                    records = await agmarknet_provider.daily_observations(
                        report_date, target, market_index
                    )
                    return (target, report_date, records, None)
                except AgmarknetError as e:
                    return (target, report_date, [], e)

        jobs = [
            _fetch_one(report_date, target)
            for report_date in dates
            for target in targets
        ]
        fetched_batches = await asyncio.gather(*jobs)

        # Phase 2: store sequentially in deterministic state/date order.
        fetched_batches.sort(
            key=lambda item: (item[1].isoformat(), item[0].name)
        )
        for target, report_date, records, fetch_error in fetched_batches:
            if stored_total >= settings.MARKET_INGEST_MAX_RECORDS:
                capped = True
                break
            day = report_date.isoformat()
            if fetch_error is not None:
                # One state/date failing must not discard the states
                # that already succeeded (or the ones still to come).
                failed_parts.append(f"{target.name}@{day}: {fetch_error}")
                logger.warning(
                    "market_ingest_state_failed",
                    state=target.name,
                    date=day,
                    error=str(fetch_error),
                )
                continue
            if district:
                wanted = district.strip().lower()
                kept = [
                    r for r in records
                    if str(r.get("district", "")).strip().lower() == wanted
                ]
                skipped_total += len(records) - len(kept)
                records = kept
            fetched_total += len(records)
            stored, skipped, day_min, day_max = (
                await market_service.ingest_records(
                    session,
                    records,
                    resource_id=SOURCE_URL,
                    state_filter=target.name,
                )
            )
            stored_total += stored
            skipped_total += skipped
            if day_min and (min_seen is None or day_min < min_seen):
                min_seen = day_min
            if day_max and (max_seen is None or day_max > max_seen):
                max_seen = day_max

        ingestion.fetched_count = fetched_total
        ingestion.stored_count = stored_total
        ingestion.skipped_count = skipped_total
        ingestion.min_observation_date = min_seen
        ingestion.max_observation_date = max_seen
        finished_at = datetime.now(timezone.utc)
        duration_s = round((finished_at - started_at).total_seconds(), 1)
        if capped:
            ingestion.status = "capped"
            ingestion.error = (
                "Stored observations reached MARKET_INGEST_MAX_RECORDS; "
                "this is a partial pull. Continue with per-state runs."
            )
        elif failed_parts and stored_total == 0:
            ingestion.status = "failed"
            ingestion.error = "; ".join(failed_parts)[:2000]
        else:
            ingestion.status = "success"
            if failed_parts:
                ingestion.error = (
                    "Partial run, failed windows: "
                    + "; ".join(failed_parts)[:1900]
                )
        ingestion.finished_at = finished_at
        await session.flush()
        await session.commit()
        logger.info(
            "market_ingest_completed",
            provider=PROVIDER_NAME,
            scope=state or "national",
            fetched=fetched_total,
            stored=stored_total,
            skipped=skipped_total,
            capped=capped,
            failed_windows=len(failed_parts),
            duration_s=duration_s,
            status=ingestion.status,
        )
        if capped:
            return {
                "status": "capped",
                "fetched": fetched_total,
                "stored": stored_total,
            }
        if ingestion.status == "failed":
            return {"status": "failed", "error": ingestion.error}
        return {
            "status": "success",
            "fetched": fetched_total,
            "stored": stored_total,
        }
