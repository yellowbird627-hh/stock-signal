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


def _sig(score: int, max_score: int, detail: str) -> dict:
    return {"score": score, "max": max_score, "detail": detail}


# ── BUY 신호 계산 ─────────────────────────────────────────────────────────────

def _score_buy(flow: dict, tech: dict, sentiment_score: float, market: str) -> dict:
    is_us = market == "US"

    # B1 — 기관+외국인 동반 순매수
    if not is_us:
        streak = flow.get("buy_streak", 0)
        b1 = _sig(
            25 if streak >= 3 else 12 if streak == 2 else 0, 25,
            f"기관+외국인 {streak}일 연속 순매수" if streak > 0 else "기관+외국인 동반 순매수 없음",
        )
    else:
        b1 = _sig(0, 0, "미국 주식: 일별 기관 데이터 없음 (타 지표 재분배)")

    # B2 — 30일 고점 대비 하락
    drop = tech["price_position"]["drop_from_high_pct"]
    b2 = _sig(15 if drop >= 10 else 8 if drop >= 5 else 0, 15, f"30일 고점 대비 -{drop:.1f}%")

    # B3 — 뉴스 감성 (긍정)
    b3 = _sig(round(sentiment_score * 15), 15, f"긍정 신뢰도 {sentiment_score:.2f}")

    # B4 — RSI 과매도 (미국: +10pt 재분배)
    rsi = tech["rsi"]
    b4_base = 10 if rsi < 35 else 5 if rsi <= 45 else 0
    b4 = _sig(min(b4_base + 10, 20) if is_us else b4_base, 20 if is_us else 10, f"RSI {rsi}")

    # B5 — MACD 골든크로스
    crossed_up = tech["macd"]["crossed_up"]
    b5 = _sig(8 if crossed_up else 0, 8, "MACD 골든크로스 발생" if crossed_up else "MACD 크로스 없음")

    # B6 — 거래량 급증 + 양봉
    vol = tech["volume"]
    b6 = _sig(
        5 if vol["bullish_spike"] else 0, 5,
        f"거래량 {vol['ratio']:.1f}배 {'+ 양봉' if vol['bullish_spike'] else ''}",
    )

    # B7 — 볼린저 하단 (미국: +7pt 재분배)
    bb = tech["bollinger"]
    b7_base = 8 if bb["recovery_lower"] else 4 if bb["touch_lower"] else 0
    b7_detail = ("볼린저 하단 이탈 후 복귀" if bb["recovery_lower"]
                 else "볼린저 하단 터치" if bb["touch_lower"] else "볼린저 하단 신호 없음")
    b7 = _sig(min(b7_base + 7, 15) if is_us else b7_base, 15 if is_us else 8, b7_detail)

    # B8 — 스토캐스틱 과매도 (미국: +8pt 재분배)
    sto = tech["stochastic"]
    b8_base = 7 if (sto["cross_up"] and sto["k"] < 20) else 3 if sto["k"] < 20 else 0
    b8_detail = f"스토캐스틱 K={sto['k']:.1f}" + (" + 상향크로스" if sto["cross_up"] else "")
    b8 = _sig(min(b8_base + 8, 15) if is_us else b8_base, 15 if is_us else 7, b8_detail)

    # B9 — 공매도 감소 / Put-Call 하락
    if not is_us:
        days = flow.get("short_decrease_days", 0)
        b9 = _sig(
            4 if days >= 3 else 2 if days >= 1 else 0, 4,
            f"공매도 비율 {days}일 연속 감소" if days > 0 else "공매도 감소 없음",
        )
    else:
        pc = flow.get("put_call_ratio_trend", 0)
        b9 = _sig(4 if pc < -0.1 else 0, 4, "Put/Call 비율 하락 중" if pc < -0.1 else "Put/Call 중립")

    # B10 — 이동평균 정배열
    ma = tech["ma_alignment"]
    b10 = _sig(
        3 if ma["bullish"] else 1 if ma["partial_bullish"] else 0, 3,
        "완전 정배열 (5>20>60)" if ma["bullish"]
        else "부분 정배열 (5>20)" if ma["partial_bullish"] else "정배열 아님",
    )

    return {
        "b1_institutional_flow": b1,
        "b2_price_drop":         b2,
        "b3_news_sentiment":     b3,
        "b4_rsi":                b4,
        "b5_macd":               b5,
        "b6_volume":             b6,
        "b7_bollinger":          b7,
        "b8_stochastic":         b8,
        "b9_short_ratio":        b9,
        "b10_ma_alignment":      b10,
    }


# ── SELL 신호 계산 ────────────────────────────────────────────────────────────

def _score_sell(flow: dict, tech: dict, sentiment_score: float, market: str) -> dict:
    is_us = market == "US"
    neg_score = 1.0 - sentiment_score

    # S1 — 기관+외국인 동반 순매도
    if not is_us:
        streak = flow.get("sell_streak", 0)
        s1 = _sig(
            25 if streak >= 3 else 12 if streak == 2 else 0, 25,
            f"기관+외국인 {streak}일 연속 순매도" if streak > 0 else "기관+외국인 동반 순매도 없음",
        )
    else:
        s1 = _sig(0, 0, "미국 주식: 일별 기관 데이터 없음 (타 지표 재분배)")

    # S2 — 30일 저점 대비 상승
    rise = tech["price_position"]["rise_from_low_pct"]
    s2 = _sig(15 if rise >= 10 else 8 if rise >= 5 else 0, 15, f"30일 저점 대비 +{rise:.1f}%")

    # S3 — 뉴스 감성 (부정)
    s3 = _sig(round(neg_score * 15), 15, f"부정 신뢰도 {neg_score:.2f}")

    # S4 — RSI 과매수 (미국: +10pt 재분배)
    rsi = tech["rsi"]
    s4_base = 10 if rsi > 70 else 5 if rsi >= 60 else 0
    s4 = _sig(min(s4_base + 10, 20) if is_us else s4_base, 20 if is_us else 10, f"RSI {rsi}")

    # S5 — MACD 데드크로스
    crossed_down = tech["macd"]["crossed_down"]
    s5 = _sig(8 if crossed_down else 0, 8, "MACD 데드크로스 발생" if crossed_down else "MACD 크로스 없음")

    # S6 — 거래량 급증 + 음봉
    vol = tech["volume"]
    s6 = _sig(
        5 if vol["bearish_spike"] else 0, 5,
        f"거래량 {vol['ratio']:.1f}배 {'+ 음봉' if vol['bearish_spike'] else ''}",
    )

    # S7 — 볼린저 상단 (미국: +7pt 재분배)
    bb = tech["bollinger"]
    s7_base = 8 if bb["recovery_upper"] else 4 if bb["touch_upper"] else 0
    s7_detail = ("볼린저 상단 이탈 후 복귀" if bb["recovery_upper"]
                 else "볼린저 상단 터치" if bb["touch_upper"] else "볼린저 상단 신호 없음")
    s7 = _sig(min(s7_base + 7, 15) if is_us else s7_base, 15 if is_us else 8, s7_detail)

    # S8 — 스토캐스틱 과매수 (미국: +8pt 재분배)
    sto = tech["stochastic"]
    s8_base = 7 if (sto["cross_down"] and sto["k"] > 80) else 3 if sto["k"] > 80 else 0
    s8_detail = f"스토캐스틱 K={sto['k']:.1f}" + (" + 하향크로스" if sto["cross_down"] else "")
    s8 = _sig(min(s8_base + 8, 15) if is_us else s8_base, 15 if is_us else 7, s8_detail)

    # S9 — 공매도 증가 / Put-Call 상승
    if not is_us:
        days = flow.get("short_increase_days", 0)
        s9 = _sig(
            4 if days >= 3 else 2 if days >= 1 else 0, 4,
            f"공매도 비율 {days}일 연속 급증" if days > 0 else "공매도 급증 없음",
        )
    else:
        pc = flow.get("put_call_ratio_trend", 0)
        s9 = _sig(4 if pc > 0.1 else 0, 4, "Put/Call 비율 상승 중" if pc > 0.1 else "Put/Call 중립")

    # S10 — 이동평균 역배열
    ma = tech["ma_alignment"]
    s10 = _sig(
        3 if ma["bearish"] else 1 if ma["partial_bearish"] else 0, 3,
        "완전 역배열 (5<20<60)" if ma["bearish"]
        else "부분 역배열 (5<20)" if ma["partial_bearish"] else "역배열 아님",
    )

    return {
        "s1_institutional_flow": s1,
        "s2_price_rise":         s2,
        "s3_news_sentiment":     s3,
        "s4_rsi":                s4,
        "s5_macd":               s5,
        "s6_volume":             s6,
        "s7_bollinger":          s7,
        "s8_stochastic":         s8,
        "s9_short_ratio":        s9,
        "s10_ma_alignment":      s10,
    }


# ── 컨플루언스 보너스 ─────────────────────────────────────────────────────────

def _confluence_buy(b: dict) -> tuple[int, int]:
    categories = {
        "기관외국인": b["b1_institutional_flow"]["score"] > 0,
        "가격위치":   b["b2_price_drop"]["score"] > 0,
        "뉴스":       b["b3_news_sentiment"]["score"] >= 10,
        "오실레이터": b["b4_rsi"]["score"] + b["b8_stochastic"]["score"] >= 8,
        "추세":       b["b5_macd"]["score"] > 0 or b["b10_ma_alignment"]["score"] > 0,
        "거래량":     b["b6_volume"]["score"] > 0 or b["b9_short_ratio"]["score"] > 0,
    }
    triggered = sum(1 for v in categories.values() if v)
    return (10 if triggered >= 4 else 0), triggered


def _confluence_sell(s: dict) -> tuple[int, int]:
    categories = {
        "기관외국인": s["s1_institutional_flow"]["score"] > 0,
        "가격위치":   s["s2_price_rise"]["score"] > 0,
        "뉴스":       s["s3_news_sentiment"]["score"] >= 10,
        "오실레이터": s["s4_rsi"]["score"] + s["s8_stochastic"]["score"] >= 8,
        "추세":       s["s5_macd"]["score"] > 0 or s["s10_ma_alignment"]["score"] > 0,
        "거래량":     s["s6_volume"]["score"] > 0 or s["s9_short_ratio"]["score"] > 0,
    }
    triggered = sum(1 for v in categories.values() if v)
    return (10 if triggered >= 4 else 0), triggered


# ── 메인 집계 ─────────────────────────────────────────────────────────────────

def compute_scores(flow: dict, tech: dict, sentiment_score: float, market: str) -> dict:
    b = _score_buy(flow, tech, sentiment_score, market)
    s = _score_sell(flow, tech, sentiment_score, market)

    buy_base  = sum(v["score"] for v in b.values())
    sell_base = sum(v["score"] for v in s.values())

    buy_bonus,  buy_conf_count  = _confluence_buy(b)
    sell_bonus, sell_conf_count = _confluence_sell(s)

    buy_total  = min(100, buy_base  + buy_bonus)
    sell_total = min(100, sell_base + sell_bonus)

    return {
        "buy": {
            "total": buy_total, "base": buy_base,
            "confluence_bonus": buy_bonus, "confluence_count": buy_conf_count,
            "label": _label(buy_total), "breakdown": b,
        },
        "sell": {
            "total": sell_total, "base": sell_base,
            "confluence_bonus": sell_bonus, "confluence_count": sell_conf_count,
            "label": _label(sell_total), "breakdown": s,
        },
    }
