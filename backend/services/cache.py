from __future__ import annotations
import hashlib
import time
from typing import Any, Optional

_cache: dict[str, tuple[float, Any]] = {}

CACHE_TTL = {
    "ohlcv": 900,           # 15분
    "investor_flow": 1800,  # 30분
    "short_ratio": 1800,    # 30분
    "news_headlines": 3600, # 60분
    "news_sentiment": 7200, # 120분
    "backtest": 3600,       # 60분
}


def get(key: str, layer: str) -> Optional[Any]:
    ttl = CACHE_TTL.get(layer, 900)
    entry = _cache.get(key)
    if entry:
        ts, value = entry
        if time.time() - ts < ttl:
            return value
        del _cache[key]
    return None


def set(key: str, layer: str, value: Any) -> None:
    _cache[key] = (time.time(), value)


def invalidate(key: str) -> None:
    _cache.pop(key, None)


def invalidate_ticker(ticker: str, market: str) -> None:
    prefix = f"{market}:{ticker}:"
    keys_to_del = [k for k in _cache if k.startswith(prefix)]
    for k in keys_to_del:
        del _cache[k]


def headlines_hash(headlines: list[str]) -> str:
    return hashlib.md5("|".join(headlines).encode()).hexdigest()[:8]
