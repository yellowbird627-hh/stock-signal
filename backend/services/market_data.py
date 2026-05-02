from __future__ import annotations
import pandas as pd
from datetime import datetime, timedelta
from . import cache as _cache


def fetch_ohlcv(ticker: str, market: str, days: int = 70) -> pd.DataFrame:
    """
    Returns OHLCV DataFrame with columns: Open, High, Low, Close, Volume.
    Fetches at least `days` calendar days to ensure 60 trading days for MA60.
    """
    cache_key = f"{market}:{ticker}:ohlcv"
    cached = _cache.get(cache_key, "ohlcv")
    if cached is not None:
        return cached

    end = datetime.today()
    start = end - timedelta(days=days)

    if market == "KRX":
        df = _fetch_krx(ticker, start, end)
    elif market == "US":
        df = _fetch_us(ticker, start, end)
    else:
        raise ValueError(f"Unsupported market: {market}")

    df = df.dropna()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index(ascending=True)

    _cache.set(cache_key, "ohlcv", df)
    return df


def _fetch_krx(ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
    import FinanceDataReader as fdr
    ticker = ticker.zfill(6)
    df = fdr.DataReader(ticker, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
    df = df.rename(columns={"Open": "Open", "High": "High", "Low": "Low",
                             "Close": "Close", "Volume": "Volume"})
    return df[["Open", "High", "Low", "Close", "Volume"]]


def _fetch_us(ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
    import yfinance as yf
    raw = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                      end=end.strftime("%Y-%m-%d"), progress=False, auto_adjust=True)
    if raw.empty:
        raise ValueError(f"No data returned for {ticker}")
    # yfinance may return MultiIndex columns
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    return raw[["Open", "High", "Low", "Close", "Volume"]]


def get_fundamentals(ticker: str, market: str) -> dict:
    """PER/PBR 조회. 장외/주말 또는 데이터 없으면 None 반환."""
    cache_key = f"{market}:{ticker}:fundamentals"
    cached = _cache.get(cache_key, "fundamentals")
    if cached is not None:
        return cached

    result: dict = {"per": None, "pbr": None}
    try:
        if market == "KRX":
            result = _get_krx_fundamentals(ticker)
        elif market == "US":
            result = _get_us_fundamentals(ticker)
    except Exception:
        pass

    _cache.set(cache_key, "fundamentals", result)
    return result


def _get_krx_fundamentals(ticker: str) -> dict:
    from pykrx import stock as krx_stock
    ticker = ticker.zfill(6)
    for days_back in range(0, 4):
        date = (datetime.today() - timedelta(days=days_back)).strftime("%Y%m%d")
        try:
            df = krx_stock.get_market_fundamental(date, date, ticker)
            if df is not None and not df.empty and "PER" in df.columns:
                per = float(df["PER"].iloc[0])
                pbr = float(df["PBR"].iloc[0])
                return {
                    "per": round(per, 2) if per > 0 else None,
                    "pbr": round(pbr, 2) if pbr > 0 else None,
                }
        except Exception:
            continue
    return {"per": None, "pbr": None}


def _get_us_fundamentals(ticker: str) -> dict:
    import yfinance as yf
    info = yf.Ticker(ticker).info
    per = info.get("trailingPE")
    pbr = info.get("priceToBook")
    return {
        "per": round(float(per), 2) if per is not None else None,
        "pbr": round(float(pbr), 2) if pbr is not None else None,
    }


def get_company_name(ticker: str, market: str) -> str:
    try:
        if market == "KRX":
            import FinanceDataReader as fdr
            listing = fdr.StockListing("KRX")
            row = listing[listing["Code"] == ticker.zfill(6)]
            if not row.empty:
                return row.iloc[0].get("Name", ticker)
        elif market == "US":
            import yfinance as yf
            info = yf.Ticker(ticker).info
            return info.get("shortName", ticker)
    except Exception:
        pass
    return ticker
