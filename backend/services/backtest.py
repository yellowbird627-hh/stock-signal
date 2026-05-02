"""
과거 OHLCV 기반 신호 백테스팅.
기관/외국인·뉴스 감성은 과거 데이터 미보유 → 중립값(0 / 0.5) 처리.
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta

import pandas as pd

from . import cache as _cache, technical, scorer

logger = logging.getLogger(__name__)


def _fetch_ohlcv(ticker: str, market: str) -> pd.DataFrame:
    """백테스팅용 300일 OHLCV — 일반 캐시와 분리."""
    cache_key = f"{market}:{ticker}:ohlcv_bt"
    cached = _cache.get(cache_key, "backtest")
    if cached is not None:
        return cached

    end = datetime.today()
    start = end - timedelta(days=300)

    if market == "KRX":
        import FinanceDataReader as fdr
        t = ticker.zfill(6)
        df = fdr.DataReader(t, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
    else:
        import yfinance as yf
        df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                         end=end.strftime("%Y-%m-%d"), progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index(ascending=True)

    _cache.set(cache_key, "backtest", df)
    return df


_NEUTRAL_FLOW = {
    "buy_streak": 0, "sell_streak": 0,
    "short_decrease_days": 0, "short_increase_days": 0,
    "put_call_ratio_trend": 0,
}


def run_backtest(ticker: str, market: str,
                 threshold: int = 25, hold_days: int = 5) -> dict:
    """
    threshold 이상 매수 신호가 발생한 날 → hold_days 후 수익률 집계.
    """
    cache_key = f"{market}:{ticker}:bt:{threshold}:{hold_days}"
    cached = _cache.get(cache_key, "backtest")
    if cached is not None:
        return cached

    try:
        df = _fetch_ohlcv(ticker, market)
    except Exception as e:
        return {"error": f"데이터 수집 실패: {e}"}

    min_rows = 70 + hold_days
    if len(df) < min_rows:
        return {"error": f"데이터 부족 (보유 {len(df)}일, 최소 {min_rows}일 필요)"}

    signals = []

    for i in range(70, len(df) - hold_days):
        df_slice = df.iloc[:i + 1]
        try:
            tech = technical.compute_all(df_slice)
            scores = scorer.compute_scores(_NEUTRAL_FLOW, tech, 0.5, market)
        except Exception:
            continue

        buy_score = scores["buy"]["total"]
        if buy_score < threshold:
            continue

        entry = float(df.iloc[i]["Close"])
        exit_ = float(df.iloc[i + hold_days]["Close"])
        ret = (exit_ - entry) / entry * 100

        signals.append({
            "date":        df.index[i].strftime("%Y-%m-%d"),
            "score":       buy_score,
            "label":       scores["buy"]["label"],
            "entry_price": round(entry, 2),
            "exit_price":  round(exit_, 2),
            "return_pct":  round(ret, 2),
            "win":         ret > 0,
        })

    if not signals:
        result = {
            "ticker": ticker, "market": market,
            "threshold": threshold, "hold_days": hold_days,
            "total_signals": 0,
            "win_rate": 0.0, "avg_return_pct": 0.0,
            "max_loss_pct": 0.0, "max_gain_pct": 0.0,
            "signals": [],
        }
    else:
        returns = [s["return_pct"] for s in signals]
        wins    = [s for s in signals if s["win"]]
        result = {
            "ticker": ticker, "market": market,
            "threshold": threshold, "hold_days": hold_days,
            "total_signals":  len(signals),
            "win_rate":       round(len(wins) / len(signals), 3),
            "avg_return_pct": round(sum(returns) / len(returns), 2),
            "max_loss_pct":   round(min(returns), 2),
            "max_gain_pct":   round(max(returns), 2),
            "signals":        signals,
        }

    _cache.set(cache_key, "backtest", result)
    return result
