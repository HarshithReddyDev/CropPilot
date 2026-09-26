"""Bounded LRU model cache. Only selected specialists load; warm models
are reused; least-recently-used evicted past max_loaded_models."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Callable


class ModelCache:
    def __init__(self, max_loaded_models: int = 3):
        self.max_loaded = max(1, max_loaded_models)
        self._items: OrderedDict[str, object] = OrderedDict()
        self._lock = threading.Lock()
        self.loads = 0
        self.evictions = 0
        self.errors = 0

    def get_or_load(self, model_id: str, loader: Callable[[], object]) -> object:
        with self._lock:
            if model_id in self._items:
                self._items.move_to_end(model_id)
                return self._items[model_id]
        try:
            model = loader()
        except Exception:
            with self._lock:
                self.errors += 1
            raise
        with self._lock:
            self._items[model_id] = model
            self._items.move_to_end(model_id)
            self.loads += 1
            while len(self._items) > self.max_loaded:
                old_id, old = self._items.popitem(last=False)
                self.evictions += 1
                unload = getattr(old, "unload", None)
                try:
                    if callable(unload):
                        unload()
                except Exception:
                    pass
            return model

    def get(self, model_id: str) -> object | None:
        with self._lock:
            m = self._items.get(model_id)
            if m is not None:
                self._items.move_to_end(model_id)
            return m

    def loaded_ids(self) -> list[str]:
        with self._lock:
            return list(self._items.keys())

    def clear(self) -> None:
        with self._lock:
            for m in self._items.values():
                try:
                    u = getattr(m, "unload", None)
                    if callable(u):
                        u()
                except Exception:
                    pass
            self._items.clear()
