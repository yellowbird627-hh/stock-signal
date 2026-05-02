"""
기관/외국인 순매수·매도 연속일 + 공매도 비율 추이 계산 (KRX)
미국 주식: Put/Call Ratio 방향성 추정

pykrx 사용. KRX 공매도·투자자 API는 주말/공휴일에 데이터 미제공.
장외 시간에는 마지막 거래일 데이터를 파일 캐시에서 불러와 표시.
"""

from __future__ import annotations
import json
import logging
import os
from datetime import datetime, timedelta

from pykrx import stock as krx_stock

from . import cache as _cache

logger = logging.getLogger(__name__)

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "flow_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)


def _file_path(ticker: str, kind: str) -> str:
    return os.path.join(_CACHE_DIR, f"KRX_{ticker}_{kind}.json")


def _save_to_file(ticker: str, kind: str, data: dict) -> None:
    try:
        with open(_file_path(ticker, kind), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        logger.warning("파일 캐시 저장 실패 (%s/%s): %s", ticker, kind, e)


def _load_from_file(ticker: str, kind: str) -> dict | None:
    path = _file_path(ticker, kind)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_investor_flow_krx(ticker: str) -> dict:
    cache_key = f"KRX:{ticker}:investor_flow"
    cached = _cache.get(cache_key, "investor_flow")
    if cached is not None:
        return cached

    try:
        t = ticker.zfill(6)
        end = datetime.today()
        start = end - timedelta(days=20)

        df = krx_stock.get_market_trading_value_by_date(
            start.strftime("%Y%m%d"),
            end.strftime("%Y%m%d"),
            t,
            on="순매수",
        )

        if df.empty or "기관합계" not in df.columns:
            raise ValueError("빈 응답 (장외 시간)")

        df = df.sort_index(ascending=False)
        last_date = df.index[0].strftime("%m-%d")
        buy_streak = sell_streak = 0

        for _, row in df.iterrows():
            inst = float(row.get("기관합계", 0) or 0)
            fore = float(row.get("외국인합계", 0) or 0)
            if inst > 0 and fore > 0:
                if sell_streak > 0:
                    break
                buy_streak += 1
            elif inst < 0 and fore < 0:
                if buy_streak > 0:
                    break
                sell_streak += 1
            else:
                break

        result = {"buy_streak": buy_streak, "sell_streak": sell_streak,
                  "last_date": last_date, "data_error": None}
        _save_to_file(ticker, "investor_flow", result)

    except Exception as e:
        logger.warning("investor_flow 오류 (%s): %s", ticker, e)
        saved = _load_from_file(ticker, "investor_flow")
        if saved:
            result = {**saved, "data_error": f"{saved.get('last_date', '?')} 마지막 거래일 기준"}
        else:
            result = {**_fallback_flow(), "data_error": "데이터 없음 (첫 장중 조회 필요)"}

    _cache.set(cache_key, "investor_flow", result)
    return result


def get_short_ratio_krx(ticker: str) -> dict:
    cache_key = f"KRX:{ticker}:short_ratio"
    cached = _cache.get(cache_key, "short_ratio")
    if cached is not None:
        return cached

    try:
        t = ticker.zfill(6)
        end = datetime.today()
        start = end - timedelta(days=14)

        df = krx_stock.get_shorting_volume_by_date(
            start.strftime("%Y%m%d"),
            end.strftime("%Y%m%d"),
            t,
        )

        if df.empty or "비중" not in df.columns:
            raise ValueError("빈 응답 (장외 시간)")

        df = df.sort_index(ascending=False)
        last_date = df.index[0].strftime("%m-%d")
        ratios = df["비중"].dropna().tolist()
        decrease_days = increase_days = 0

        for i in range(len(ratios) - 1):
            if ratios[i] < ratios[i + 1]:
                if increase_days > 0:
                    break
                decrease_days += 1
            elif ratios[i] > ratios[i + 1]:
                if decrease_days > 0:
                    break
                increase_days += 1
            else:
                break

        result = {"short_decrease_days": decrease_days,
                  "short_increase_days": increase_days,
                  "last_date": last_date, "data_error": None}
        _save_to_file(ticker, "short_ratio", result)

    except Exception as e:
        logger.warning("공매도 데이터 오류 (%s): %s", ticker, e)
        saved = _load_from_file(ticker, "short_ratio")
        if saved:
            result = {**saved, "data_error": f"{saved.get('last_date', '?')} 마지막 거래일 기준"}
        else:
            result = {"short_decrease_days": 0, "short_increase_days": 0,
                      "data_error": "데이터 없음 (첫 장중 조회 필요)"}

    _cache.set(cache_key, "short_ratio", result)
    return result


def get_put_call_ratio_us(ticker: str) -> dict:
    """미국 주식: yfinance options chain으로 Put/Call 비율 방향 추정."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        dates = t.options
        if not dates:
            return {"put_call_ratio_trend": 0, "data_error": "옵션 데이터 없음"}

        chain = t.option_chain(dates[0])
        put_vol = chain.puts["volume"].sum()
        call_vol = chain.calls["volume"].sum()
        ratio = put_vol / call_vol if call_vol > 0 else 1.0

        trend = ratio - 1.0
        return {"put_call_ratio": round(float(ratio), 3),
                "put_call_ratio_trend": round(float(trend), 3), "data_error": None}
    except Exception as e:
        return {"put_call_ratio_trend": 0, "data_error": str(e)}


def get_flow(ticker: str, market: str) -> dict:
    if market == "KRX":
        flow = get_investor_flow_krx(ticker)
        short = get_short_ratio_krx(ticker)
        return {**flow, **short}
    else:
        return {**_fallback_flow(), **get_put_call_ratio_us(ticker)}


def _fallback_flow() -> dict:
    return {"buy_streak": 0, "sell_streak": 0,
            "short_decrease_days": 0, "short_increase_days": 0}
