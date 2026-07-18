from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import text

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
