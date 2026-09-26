"""Bounded parallel specialist executor.

asyncio + thread offload (models release no GIL guarantee; PyTorch CPU
contends, so concurrency is bounded). Per-model timeout, cancellation,
latency recorded per specialist. Never duplicates a model to pad counts.
"""

from __future__ import annotations

import asyncio
import time

from services.disease.base import DiseasePrediction
from services.disease.errors import INFERENCE_TIMEOUT, MODEL_INFERENCE_FAILED


async def run_specialists(
    adapters: list,
    image,
    region_kind: str = "full",
    region_box: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0),
    max_parallel: int = 3,
    timeout_s: float = 20.0,
) -> tuple[list[DiseasePrediction], dict[str, float], list[dict]]:
    sem = asyncio.Semaphore(max(1, max_parallel))
    latencies: dict[str, float] = {}
    runs: list[dict] = []

    async def _one(adapter) -> DiseasePrediction | None:
        async with sem:
            t0 = time.perf_counter()
            try:
                pred = await asyncio.wait_for(
                    asyncio.to_thread(adapter.predict, image, region_kind, region_box),
                    timeout=timeout_s,
                )
                latencies[adapter.model_id] = (time.perf_counter() - t0) * 1000.0
                runs.append({"model_id": adapter.model_id, "ok": True})
                return pred
            except asyncio.TimeoutError:
                latencies[adapter.model_id] = (time.perf_counter() - t0) * 1000.0
                runs.append({"model_id": adapter.model_id, "ok": False,
                             "error": "timeout", "error_code": INFERENCE_TIMEOUT})
                return None
            except Exception as e:
                latencies[adapter.model_id] = (time.perf_counter() - t0) * 1000.0
                runs.append({"model_id": adapter.model_id, "ok": False,
                             "error": f"{type(e).__name__}: {e}", "error_code": MODEL_INFERENCE_FAILED})
                return None

    results = await asyncio.gather(*[_one(a) for a in adapters])
    return [r for r in results if r is not None], latencies, runs
