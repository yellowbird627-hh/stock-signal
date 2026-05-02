import numpy as np
import pandas as pd


# ── RSI ──────────────────────────────────────────────────────────────────────

def compute_rsi(closes: list[float], period: int = 14) -> float:
    arr = np.array(closes, dtype=float)
    deltas = np.diff(arr)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    if len(deltas) < period:
        return 50.0

    avg_gain = gains[:period].mean()
    avg_loss = losses[:period].mean()

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


# ── MACD ─────────────────────────────────────────────────────────────────────

def compute_macd(closes: list[float]) -> dict:
    s = pd.Series(closes, dtype=float)
    ema12 = s.ewm(span=12, adjust=False).mean()
    ema26 = s.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line

    hist = histogram.tolist()
    crossed_up = len(hist) >= 2 and hist[-2] < 0 and hist[-1] > 0
    crossed_down = len(hist) >= 2 and hist[-2] > 0 and hist[-1] < 0

    return {
        "macd": round(float(macd_line.iloc[-1]), 4),
        "signal": round(float(signal_line.iloc[-1]), 4),
        "histogram": round(float(histogram.iloc[-1]), 4),
        "crossed_up": crossed_up,
        "crossed_down": crossed_down,
    }


# ── 볼린저 밴드 ───────────────────────────────────────────────────────────────

def compute_bollinger(closes: list[float], period: int = 20, std_mult: float = 2.0) -> dict:
    s = pd.Series(closes, dtype=float)
    ma = s.rolling(period).mean()
    std = s.rolling(period).std()
    upper = (ma + std_mult * std).tolist()
    lower = (ma - std_mult * std).tolist()

    current = closes[-1]
    prev = closes[-2] if len(closes) >= 2 else current

    lower_cur = lower[-1]
    lower_prev = lower[-2] if len(lower) >= 2 else lower_cur
    upper_cur = upper[-1]
    upper_prev = upper[-2] if len(upper) >= 2 else upper_cur

    touch_lower = current <= lower_cur
    recovery_lower = prev <= lower_prev and current > lower_cur  # 이탈 후 복귀
    touch_upper = current >= upper_cur
    recovery_upper = prev >= upper_prev and current < upper_cur

    return {
        "upper": round(float(upper_cur), 2),
        "lower": round(float(lower_cur), 2),
        "mid": round(float(ma.iloc[-1]), 2),
        "touch_lower": touch_lower,
        "recovery_lower": recovery_lower,
        "touch_upper": touch_upper,
        "recovery_upper": recovery_upper,
    }


# ── 스토캐스틱 ────────────────────────────────────────────────────────────────

def compute_stochastic(highs: list[float], lows: list[float],
                       closes: list[float], k_period: int = 14, d_period: int = 3) -> dict:
    h = pd.Series(highs, dtype=float)
    l = pd.Series(lows, dtype=float)
    c = pd.Series(closes, dtype=float)

    lowest_low = l.rolling(k_period).min()
    highest_high = h.rolling(k_period).max()
    denom = highest_high - lowest_low
    k = 100 * (c - lowest_low) / denom.replace(0, np.nan)
    k = k.fillna(50)
    d = k.rolling(d_period).mean()

    k_list = k.tolist()
    d_list = d.tolist()

    cross_up = (len(k_list) >= 2 and len(d_list) >= 2
                and k_list[-2] < d_list[-2] and k_list[-1] > d_list[-1])
    cross_down = (len(k_list) >= 2 and len(d_list) >= 2
                  and k_list[-2] > d_list[-2] and k_list[-1] < d_list[-1])

    return {
        "k": round(float(k.iloc[-1]), 2),
        "d": round(float(d.iloc[-1]), 2),
        "cross_up": cross_up,
        "cross_down": cross_down,
    }


# ── ATR (단타 적합도) ─────────────────────────────────────────────────────────

def compute_atr(highs: list[float], lows: list[float],
                closes: list[float], period: int = 14) -> dict:
    tr_list = []
    for i in range(1, len(closes)):
        h, l, pc = highs[i], lows[i], closes[i - 1]
        tr_list.append(max(h - l, abs(h - pc), abs(l - pc)))

    if not tr_list:
        return {"atr": 0, "atr_pct": 0, "suitability": "low"}

    atr = pd.Series(tr_list).ewm(span=period, adjust=False).mean().iloc[-1]
    atr_pct = atr / closes[-1] * 100

    if atr_pct > 2.5:
        suitability = "high"
    elif atr_pct > 1.0:
        suitability = "medium"
    else:
        suitability = "low"

    return {"atr": round(float(atr), 4), "atr_pct": round(float(atr_pct), 2),
            "suitability": suitability}


# ── 이동평균 정배열 ────────────────────────────────────────────────────────────

def compute_ma_alignment(closes: list[float]) -> dict:
    s = pd.Series(closes, dtype=float)
    ma5 = float(s.rolling(5).mean().iloc[-1])
    ma20 = float(s.rolling(20).mean().iloc[-1])
    ma60 = float(s.rolling(60).mean().iloc[-1]) if len(closes) >= 60 else float("nan")

    bullish = ma5 > ma20 > ma60 if not np.isnan(ma60) else ma5 > ma20
    bearish = ma5 < ma20 < ma60 if not np.isnan(ma60) else ma5 < ma20

    partial_bullish = (ma5 > ma20) and not bullish
    partial_bearish = (ma5 < ma20) and not bearish

    return {
        "ma5": round(ma5, 2),
        "ma20": round(ma20, 2),
        "ma60": round(ma60, 2) if not np.isnan(ma60) else None,
        "bullish": bullish,
        "bearish": bearish,
        "partial_bullish": partial_bullish,
        "partial_bearish": partial_bearish,
    }


# ── 거래량 급증 ───────────────────────────────────────────────────────────────

def compute_volume_signal(volumes: list[float], opens: list[float],
                          closes: list[float], avg_period: int = 20) -> dict:
    if len(volumes) < avg_period + 1:
        return {"spike": False, "bullish_spike": False, "bearish_spike": False, "ratio": 0}

    avg_vol = float(pd.Series(volumes[-avg_period - 1:-1]).mean())
    today_vol = volumes[-1]
    ratio = today_vol / avg_vol if avg_vol > 0 else 0

    spike = ratio >= 1.5
    is_green = closes[-1] >= opens[-1]

    return {
        "spike": spike,
        "bullish_spike": spike and is_green,
        "bearish_spike": spike and not is_green,
        "ratio": round(ratio, 2),
    }


# ── 고점/저점 대비 위치 ───────────────────────────────────────────────────────

def compute_price_position(highs: list[float], lows: list[float],
                           closes: list[float], window: int = 30) -> dict:
    recent_h = highs[-window:]
    recent_l = lows[-window:]
    current = closes[-1]

    high_30 = max(recent_h)
    low_30 = min(recent_l)

    drop_from_high = (high_30 - current) / high_30 * 100 if high_30 > 0 else 0
    rise_from_low = (current - low_30) / low_30 * 100 if low_30 > 0 else 0

    return {
        "current": current,
        "high_30d": round(high_30, 2),
        "low_30d": round(low_30, 2),
        "drop_from_high_pct": round(drop_from_high, 2),
        "rise_from_low_pct": round(rise_from_low, 2),
    }


# ── 통합 기술 지표 계산 ───────────────────────────────────────────────────────

def compute_all(df) -> dict:
    closes = df["Close"].tolist()
    opens = df["Open"].tolist()
    highs = df["High"].tolist()
    lows = df["Low"].tolist()
    volumes = df["Volume"].tolist()

    return {
        "rsi": compute_rsi(closes),
        "macd": compute_macd(closes),
        "bollinger": compute_bollinger(closes),
        "stochastic": compute_stochastic(highs, lows, closes),
        "atr": compute_atr(highs, lows, closes),
        "ma_alignment": compute_ma_alignment(closes),
        "volume": compute_volume_signal(volumes, opens, closes),
        "price_position": compute_price_position(highs, lows, closes),
    }
