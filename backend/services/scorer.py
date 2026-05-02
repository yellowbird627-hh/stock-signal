"""
신호 집계 엔진: B1-B10, S1-S10 + 컨플루언스 보너스 → BUY/SELL 점수
"""

SIGNAL_LABELS = {
    range(0, 31): "none",
    range(31, 51): "weak",
    range(51, 71): "moderate",
    range(71, 86): "strong",
    range(86, 101): "very_strong",
}


def _label(score: int) -> str:
    for r, label in SIGNAL_LABELS.items():
        if score in r:
            return label
    return "very_strong"


# ── BUY 개별 점수 계산 ────────────────────────────────────────────────────────

def _score_buy(flow: dict, tech: dict, sentiment_score: float, market: str) -> dict:
    b = {}

    # B1 — 기관+외국인 동반 순매수 (미국 주식은 재분배)
    if market == "KRX":
        streak = flow.get("buy_streak", 0)
        b["b1"] = 25 if streak >= 3 else 12 if streak == 2 else 0
        b["b1_detail"] = f"기관+외국인 {streak}일 연속 순매수" if streak > 0 else "기관+외국인 동반 순매수 없음"
        b["b1_max"] = 25
    else:
        b["b1"] = 0
        b["b1_detail"] = "미국 주식: 일별 기관 데이터 없음 (타 지표 재분배)"
        b["b1_max"] = 0  # 재분배로 처리

    # B2 — 30일 고점 대비 하락
    drop = tech["price_position"]["drop_from_high_pct"]
    b["b2"] = 15 if drop >= 10 else 8 if drop >= 5 else 0
    b["b2_detail"] = f"30일 고점 대비 -{drop:.1f}%"
    b["b2_max"] = 15

    # B3 — 뉴스 감성
    b["b3"] = round(sentiment_score * 15)
    b["b3_detail"] = f"긍정 신뢰도 {sentiment_score:.2f}"
    b["b3_max"] = 15

    # B4 — RSI 과매도
    rsi = tech["rsi"]
    b["b4"] = 10 if rsi < 35 else 5 if rsi <= 45 else 0
    # 미국 주식 B1 재분배: +10pt
    if market == "US":
        b["b4"] = min(b["b4"] + 10, 20)
        b["b4_max"] = 20
    else:
        b["b4_max"] = 10
    b["b4_detail"] = f"RSI {rsi}"

    # B5 — MACD 골든크로스
    b["b5"] = 8 if tech["macd"]["crossed_up"] else 0
    b["b5_detail"] = "MACD 골든크로스 발생" if b["b5"] else "MACD 크로스 없음"
    b["b5_max"] = 8

    # B6 — 거래량 급증 + 양봉
    vol = tech["volume"]
    b["b6"] = 5 if vol["bullish_spike"] else 0
    b["b6_detail"] = f"거래량 {vol['ratio']:.1f}배 {'+ 양봉' if vol['bullish_spike'] else ''}"
    b["b6_max"] = 5

    # B7 — 볼린저 하단
    bb = tech["bollinger"]
    b["b7"] = 8 if bb["recovery_lower"] else 4 if bb["touch_lower"] else 0
    b["b7_detail"] = ("볼린저 하단 이탈 후 복귀" if bb["recovery_lower"]
                      else "볼린저 하단 터치" if bb["touch_lower"] else "볼린저 하단 신호 없음")
    # 미국 주식 B1 재분배: +7pt
    if market == "US":
        b["b7"] = min(b["b7"] + 7, 15)
        b["b7_max"] = 15
    else:
        b["b7_max"] = 8

    # B8 — 스토캐스틱 과매도
    sto = tech["stochastic"]
    b["b8"] = 7 if (sto["cross_up"] and sto["k"] < 20) else 3 if sto["k"] < 20 else 0
    # 미국 주식 B1 재분배: +8pt
    if market == "US":
        b["b8"] = min(b["b8"] + 8, 15)
        b["b8_max"] = 15
    else:
        b["b8_max"] = 7
    b["b8_detail"] = f"스토캐스틱 K={sto['k']:.1f}" + (" + 상향크로스" if sto["cross_up"] else "")

    # B9 — 공매도 비율 감소 (KRX only)
    if market == "KRX":
        short_trend = flow.get("short_decrease_days", 0)
        b["b9"] = 4 if short_trend >= 3 else 2 if short_trend >= 1 else 0
        b["b9_detail"] = f"공매도 비율 {short_trend}일 연속 감소" if short_trend > 0 else "공매도 감소 없음"
        b["b9_max"] = 4
    else:
        pc = flow.get("put_call_ratio_trend", 0)
        b["b9"] = 4 if pc < -0.1 else 0
        b["b9_detail"] = f"Put/Call 비율 하락 중" if b["b9"] else "Put/Call 중립"
        b["b9_max"] = 4

    # B10 — 이동평균 정배열
    ma = tech["ma_alignment"]
    b["b10"] = 3 if ma["bullish"] else 1 if ma["partial_bullish"] else 0
    b["b10_detail"] = ("완전 정배열 (5>20>60)" if ma["bullish"]
                       else "부분 정배열 (5>20)" if ma["partial_bullish"] else "정배열 아님")
    b["b10_max"] = 3

    return b


# ── SELL 개별 점수 계산 ───────────────────────────────────────────────────────

def _score_sell(flow: dict, tech: dict, sentiment_score: float, market: str) -> dict:
    s = {}

    if market == "KRX":
        streak = flow.get("sell_streak", 0)
        s["s1"] = 25 if streak >= 3 else 12 if streak == 2 else 0
        s["s1_detail"] = f"기관+외국인 {streak}일 연속 순매도" if streak > 0 else "기관+외국인 동반 순매도 없음"
        s["s1_max"] = 25
    else:
        s["s1"] = 0
        s["s1_detail"] = "미국 주식: 일별 기관 데이터 없음 (타 지표 재분배)"
        s["s1_max"] = 0

    rise = tech["price_position"]["rise_from_low_pct"]
    s["s2"] = 15 if rise >= 10 else 8 if rise >= 5 else 0
    s["s2_detail"] = f"30일 저점 대비 +{rise:.1f}%"
    s["s2_max"] = 15

    neg_score = (1.0 - sentiment_score)
    s["s3"] = round(neg_score * 15)
    s["s3_detail"] = f"부정 신뢰도 {neg_score:.2f}"
    s["s3_max"] = 15

    rsi = tech["rsi"]
    s["s4"] = 10 if rsi > 70 else 5 if rsi >= 60 else 0
    if market == "US":
        s["s4"] = min(s["s4"] + 10, 20)
        s["s4_max"] = 20
    else:
        s["s4_max"] = 10
    s["s4_detail"] = f"RSI {rsi}"

    s["s5"] = 8 if tech["macd"]["crossed_down"] else 0
    s["s5_detail"] = "MACD 데드크로스 발생" if s["s5"] else "MACD 크로스 없음"
    s["s5_max"] = 8

    vol = tech["volume"]
    s["s6"] = 5 if vol["bearish_spike"] else 0
    s["s6_detail"] = f"거래량 {vol['ratio']:.1f}배 {'+ 음봉' if vol['bearish_spike'] else ''}"
    s["s6_max"] = 5

    bb = tech["bollinger"]
    s["s7"] = 8 if bb["recovery_upper"] else 4 if bb["touch_upper"] else 0
    s["s7_detail"] = ("볼린저 상단 이탈 후 복귀" if bb["recovery_upper"]
                      else "볼린저 상단 터치" if bb["touch_upper"] else "볼린저 상단 신호 없음")
    if market == "US":
        s["s7"] = min(s["s7"] + 7, 15)
        s["s7_max"] = 15
    else:
        s["s7_max"] = 8

    sto = tech["stochastic"]
    s["s8"] = 7 if (sto["cross_down"] and sto["k"] > 80) else 3 if sto["k"] > 80 else 0
    if market == "US":
        s["s8"] = min(s["s8"] + 8, 15)
        s["s8_max"] = 15
    else:
        s["s8_max"] = 7
    s["s8_detail"] = f"스토캐스틱 K={sto['k']:.1f}" + (" + 하향크로스" if sto["cross_down"] else "")

    if market == "KRX":
        short_trend = flow.get("short_increase_days", 0)
        s["s9"] = 4 if short_trend >= 3 else 2 if short_trend >= 1 else 0
        s["s9_detail"] = f"공매도 비율 {short_trend}일 연속 급증" if short_trend > 0 else "공매도 급증 없음"
        s["s9_max"] = 4
    else:
        pc = flow.get("put_call_ratio_trend", 0)
        s["s9"] = 4 if pc > 0.1 else 0
        s["s9_detail"] = "Put/Call 비율 상승 중" if s["s9"] else "Put/Call 중립"
        s["s9_max"] = 4

    ma = tech["ma_alignment"]
    s["s10"] = 3 if ma["bearish"] else 1 if ma["partial_bearish"] else 0
    s["s10_detail"] = ("완전 역배열 (5<20<60)" if ma["bearish"]
                       else "부분 역배열 (5<20)" if ma["partial_bearish"] else "역배열 아님")
    s["s10_max"] = 3

    return s


# ── 컨플루언스 보너스 ─────────────────────────────────────────────────────────

def _confluence_buy(b: dict) -> tuple[int, int]:
    categories = {
        "기관외국인": b["b1"] > 0,
        "가격위치":   b["b2"] > 0,
        "뉴스":       b["b3"] >= 10,
        "오실레이터": b["b4"] + b["b8"] >= 8,
        "추세":       b["b5"] > 0 or b["b10"] > 0,
        "거래량":     b["b6"] > 0 or b["b9"] > 0,
    }
    triggered = sum(1 for v in categories.values() if v)
    return (10 if triggered >= 4 else 0), triggered


def _confluence_sell(s: dict) -> tuple[int, int]:
    categories = {
        "기관외국인": s["s1"] > 0,
        "가격위치":   s["s2"] > 0,
        "뉴스":       s["s3"] >= 10,
        "오실레이터": s["s4"] + s["s8"] >= 8,
        "추세":       s["s5"] > 0 or s["s10"] > 0,
        "거래량":     s["s6"] > 0 or s["s9"] > 0,
    }
    triggered = sum(1 for v in categories.values() if v)
    return (10 if triggered >= 4 else 0), triggered


# ── 메인 집계 ─────────────────────────────────────────────────────────────────

def compute_scores(flow: dict, tech: dict, sentiment_score: float, market: str) -> dict:
    b = _score_buy(flow, tech, sentiment_score, market)
    s = _score_sell(flow, tech, sentiment_score, market)

    buy_base = sum(b[k] for k in b if k.startswith("b") and not k.endswith(("_detail", "_max")))
    sell_base = sum(s[k] for k in s if k.startswith("s") and not k.endswith(("_detail", "_max")))

    buy_bonus, buy_conf_count = _confluence_buy(b)
    sell_bonus, sell_conf_count = _confluence_sell(s)

    buy_total = min(100, buy_base + buy_bonus)
    sell_total = min(100, sell_base + sell_bonus)

    def buy_breakdown():
        return {
            "b1_institutional_flow": {"score": b["b1"], "max": b["b1_max"], "detail": b["b1_detail"]},
            "b2_price_drop":         {"score": b["b2"], "max": b["b2_max"], "detail": b["b2_detail"]},
            "b3_news_sentiment":     {"score": b["b3"], "max": b["b3_max"], "detail": b["b3_detail"]},
            "b4_rsi":                {"score": b["b4"], "max": b["b4_max"], "detail": b["b4_detail"]},
            "b5_macd":               {"score": b["b5"], "max": b["b5_max"], "detail": b["b5_detail"]},
            "b6_volume":             {"score": b["b6"], "max": b["b6_max"], "detail": b["b6_detail"]},
            "b7_bollinger":          {"score": b["b7"], "max": b["b7_max"], "detail": b["b7_detail"]},
            "b8_stochastic":         {"score": b["b8"], "max": b["b8_max"], "detail": b["b8_detail"]},
            "b9_short_ratio":        {"score": b["b9"], "max": b["b9_max"], "detail": b["b9_detail"]},
            "b10_ma_alignment":      {"score": b["b10"], "max": b["b10_max"], "detail": b["b10_detail"]},
        }

    def sell_breakdown():
        return {
            "s1_institutional_flow": {"score": s["s1"], "max": s["s1_max"], "detail": s["s1_detail"]},
            "s2_price_rise":         {"score": s["s2"], "max": s["s2_max"], "detail": s["s2_detail"]},
            "s3_news_sentiment":     {"score": s["s3"], "max": s["s3_max"], "detail": s["s3_detail"]},
            "s4_rsi":                {"score": s["s4"], "max": s["s4_max"], "detail": s["s4_detail"]},
            "s5_macd":               {"score": s["s5"], "max": s["s5_max"], "detail": s["s5_detail"]},
            "s6_volume":             {"score": s["s6"], "max": s["s6_max"], "detail": s["s6_detail"]},
            "s7_bollinger":          {"score": s["s7"], "max": s["s7_max"], "detail": s["s7_detail"]},
            "s8_stochastic":         {"score": s["s8"], "max": s["s8_max"], "detail": s["s8_detail"]},
            "s9_short_ratio":        {"score": s["s9"], "max": s["s9_max"], "detail": s["s9_detail"]},
            "s10_ma_alignment":      {"score": s["s10"], "max": s["s10_max"], "detail": s["s10_detail"]},
        }

    return {
        "buy": {
            "total": buy_total,
            "base": buy_base,
            "confluence_bonus": buy_bonus,
            "confluence_count": buy_conf_count,
            "label": _label(buy_total),
            "breakdown": buy_breakdown(),
        },
        "sell": {
            "total": sell_total,
            "base": sell_base,
            "confluence_bonus": sell_bonus,
            "confluence_count": sell_conf_count,
            "label": _label(sell_total),
            "breakdown": sell_breakdown(),
        },
    }
