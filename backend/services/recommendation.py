"""
포트폴리오 신호 데이터를 기반으로 Gemini AI 매수/매도 추천 생성.
"""
from __future__ import annotations
import hashlib
import json
import logging
import os
from google import genai
from google.genai import types
from . import cache as _cache

logger = logging.getLogger(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

SYSTEM_PROMPT = """한국 주식 단타 트레이딩 어드바이저. 신호 데이터 분석 후 JSON만 반환 (다른 텍스트 없이):
{"buy":[{"ticker","name","timing","reason","target1","target2","stop_loss"}],"sell":[{"ticker","name","timing","reason"}],"summary":"1-2문장"}

규칙:
- buy/sell 각 최대5개, 점수35+ 종목만
- reason에 실제 지표 수치 포함 (RSI 28, 기관 3일 연속 순매수 등)
- timing은 구체적으로 (즉시진입 / 양봉확인후 / 눌림목대기 등)
- target1=MA20 또는 BB중단, target2=30일고점 또는 BB상단, stop_loss=현재가-ATR×1.5 (모두 정수, 현재가±30% 이내)
- 장외시간 데이터는 "마지막 거래일 기준" 명시
- 신호 없으면 빈 배열"""


def get_recommendation(portfolio_stocks: list[dict]) -> dict:
    key_str = "|".join(
        f"{s['ticker']}:{s.get('buy', 0)}:{s.get('sell', 0)}"
        for s in portfolio_stocks if not s.get("error")
    )
    cache_key = f"rec:{hashlib.md5(key_str.encode()).hexdigest()[:8]}"
    cached = _cache.get(cache_key, "news_sentiment")
    if cached is not None:
        return cached

    try:
        result = _call_gemini(portfolio_stocks)
    except Exception as e:
        logger.error("recommendation 오류: %s", e)
        result = {"buy": [], "sell": [], "summary": f"AI 분석 실패: {e}"}

    _cache.set(cache_key, "news_sentiment", result)
    return result


def _call_gemini(stocks: list[dict]) -> dict:
    # 신호 없는 종목 제외 — 20점 미만은 Gemini에 전송하지 않음
    candidates = [
        s for s in stocks
        if not s.get("error") and (s.get("buy", 0) >= 20 or s.get("sell", 0) >= 20)
    ]
    # 신호 종목이 없으면 상위 3개만 참고용으로 전송
    if not candidates:
        candidates = sorted(
            [s for s in stocks if not s.get("error")],
            key=lambda x: max(x.get("buy", 0), x.get("sell", 0)),
            reverse=True,
        )[:3]

    lines = []
    for s in candidates:
        buy_signals = ", ".join(
            v.get("detail", k)
            for k, v in s.get("buy_active", {}).items()
            if v.get("score", 0) > 0
        ) or "없음"
        sell_signals = ", ".join(
            v.get("detail", k)
            for k, v in s.get("sell_active", {}).items()
            if v.get("score", 0) > 0
        ) or "없음"
        limitation = s.get("data_limitation", "")

        # 가격 레벨은 매수 후보(30점+)에만 포함
        pl = s.get("price_levels", {})
        price_info = ""
        if s.get("buy", 0) >= 30 and s.get("price") and pl:
            ma60 = pl.get("ma60") or "N/A"
            price_info = (
                f" | 현재가:{s['price']}"
                f" MA20:{pl.get('ma20','?')} MA60:{ma60}"
                f" BB중단:{pl.get('bb_mid','?')} BB상단:{pl.get('bb_upper','?')}"
                f" 30일고점:{pl.get('high_30d','?')} ATR:{pl.get('atr','?')}"
            )

        lines.append(
            f"- {s['name']} ({s['ticker']}/{s['market']}): "
            f"매수 {s.get('buy', 0)}점({s.get('buy_label', 'none')}), "
            f"매도 {s.get('sell', 0)}점({s.get('sell_label', 'none')}) "
            f"| 매수신호: {buy_signals} | 매도신호: {sell_signals}"
            + price_info
            + (f" [{limitation}]" if limitation else "")
        )

    user_content = "매수/매도 추천:\n" + "\n".join(lines)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
        ),
        contents=user_content,
    )
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
