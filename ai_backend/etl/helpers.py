from __future__ import annotations

from typing import Iterable, Any


def chunked(items: Iterable[dict[str, Any]], size: int):
    batch: list[dict[str, Any]] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch

