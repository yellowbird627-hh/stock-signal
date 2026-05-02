from __future__ import annotations
import json
import logging
import os
from google import genai
from google.genai import types
from . import cache as _cache

logger = logging.getLogger(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

BATCH_SYSTEM_PROMPT = """당신은 주식 시장 뉴스 감성 분석 전문가입니다.
여러 종목의 최근 뉴스 헤드라인을 분석해 각 종목의 주가에 미칠 영향을 평가합니다.

반드시 다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{
  "종목명1": {
    "sentiment_score": 0.0~1.0,
    "confidence": 0.0~1.0,
    "key_points": ["포인트1", "포인트2"],
    "reasoning": "한 문장 근거"
  },
  "종목명2": { ... }
}

평가 기준:
- 매출/영업이익 성장, 어닝 서프라이즈: 매우 긍정 (0.8~1.0)
- 배당 증가, 자사주 매입, 신사업 수주: 긍정 (0.6~0.8)
- 단순 시세/거래량: 중립 (0.5)
- 실적 하락, 가이던스 하향: 부정 (0.2~0.4)
- 어닝쇼크, 규제/소송/경영 리스크: 매우 부정 (0.0~0.2)
- 뉴스 없음: 중립 (0.5)"""


def analyze_batch(stocks_news: dict[str, list[dict]]) -> dict[str, dict]:
    if not stocks_news:
        return {}

    results = {}
    need_analysis: dict[str, list[dict]] = {}

    for company, news_items in stocks_news.items():
        headlines = [n["headline"] for n in news_items]
        h_hash = _cache.headlines_hash(headlines)
        cache_key = f"sentiment:{company}:{h_hash}"
        cached = _cache.get(cache_key, "news_sentiment")
        if cached is not None:
            results[company] = cached
        else:
            need_analysis[company] = news_items

    if not need_analysis:
        return results

    items = list(need_analysis.items())
    for i in range(0, len(items), 5):
        batch = dict(items[i:i + 5])
        batch_results = _call_gemini(batch)
        for company, sentiment in batch_results.items():
            news_items = need_analysis.get(company, [])
            headlines = [n["headline"] for n in news_items]
            h_hash = _cache.headlines_hash(headlines)
            cache_key = f"sentiment:{company}:{h_hash}"
            _cache.set(cache_key, "news_sentiment", sentiment)
            results[company] = sentiment

    return results


def _call_gemini(batch: dict[str, list[dict]]) -> dict[str, dict]:
    user_content = ""
    for company, news_items in batch.items():
        user_content += f"\n## {company}\n"
        if not news_items:
            user_content += "- 최근 뉴스 없음\n"
        else:
            for item in news_items[:3]:
                user_content += f"- [{item['published_at']}] {item['headline']}\n"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=BATCH_SYSTEM_PROMPT,
                temperature=0.1,
            ),
            contents=user_content,
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Gemini 응답 파싱 실패: %s", e)
        return {c: _neutral() for c in batch}
    except Exception as e:
        logger.error("Gemini API 오류: %s", e)
        return {c: _neutral() for c in batch}


def _neutral() -> dict:
    return {"sentiment_score": 0.5, "confidence": 0.0,
            "key_points": [], "reasoning": "분석 실패 — 중립 처리"}
