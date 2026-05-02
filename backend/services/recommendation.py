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

SYSTEM_PROMPT = """당신은 한국 주식 단타 전문 트레이딩 어드바이저입니다.
포트폴리오 종목별 기술적 신호 데이터와 가격 레벨을 분석해 매수/매도 추천을 제공합니다.

반드시 다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{
  "buy": [
    {
      "ticker": "종목코드",
      "name": "종목명",
      "timing": "진입 타이밍 (구체적으로, 예: 즉시 진입 가능 / 오전 30분 양봉 확인 후 / 눌림목 대기)",
      "reason": "2-3문장 근거 — 활성화된 지표 수치 포함",
      "target1": 67500,
      "target2": 71200,
      "stop_loss": 62000
    }
  ],
  "sell": [
    {
      "ticker": "종목코드",
      "name": "종목명",
      "timing": "매도 타이밍 (구체적으로, 예: 즉시 매도 / 반등 시 분할 매도 / 목표가 도달 시)",
      "reason": "2-3문장 근거 — 활성화된 지표 수치 포함"
    }
  ],
  "summary": "전체 포트폴리오 시장 분위기 1-2문장 요약"
}

규칙:
- buy: 매수 점수 35점 이상 중 상위 최대 5개만 선정
- sell: 매도 점수 35점 이상 중 상위 최대 5개만 선정
- 신호 없으면 buy/sell 빈 배열 반환
- 타이밍은 신호 조합에 따라 구체적으로 작성
- 근거에는 반드시 실제 수치 포함 (예: RSI 28, 기관 3일 연속 순매수)
- 장외 시간 데이터 사용 시 "마지막 거래일 기준" 문구 포함
- target1: 1차 목표가 — MA20 또는 볼린저 중단(BB중단) 기준, 정수
- target2: 2차 목표가 — 30일 고점 또는 볼린저 상단(BB상단) 기준, 정수
- stop_loss: 손절선 — 현재가에서 ATR×1.5 하단 또는 MA60 중 높은 값, 정수
- 목표가는 반드시 현재가 기준 ±30% 이내 현실적 수치로 제시
- target1/target2/stop_loss는 매수 추천에만 포함 (매도 추천에는 불필요)"""


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
    lines = []
    for s in stocks:
        if s.get("error"):
            continue
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
        pl = s.get("price_levels", {})
        price_info = ""
        if s.get("price") and pl:
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
            f"| 매수신호: {buy_signals} "
            f"| 매도신호: {sell_signals}"
            + price_info
            + (f" [{limitation}]" if limitation else "")
        )

    user_content = "포트폴리오 종목 신호 분석 후 매수/매도 추천:\n\n" + "\n".join(lines)

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
