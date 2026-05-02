"""
장 시작 전 전체 종목 데이터 사전 수집 스케줄러.
KRX: 평일 08:55 KST / US: 평일 21:25 KST (NYSE 개장 5분 전)
"""

from __future__ import annotations
import json
import logging
import os
import urllib.request
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def _load_stocks() -> list[dict]:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "stocks.json")
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)
    return [s for s in data.get("stocks", []) if s.get("enabled", True)]


def _prefetch_market(market: str) -> None:
    from . import market_data, investor_flow, news_scraper, sentiment

    stocks = [s for s in _load_stocks() if s["market"] == market]
    if not stocks:
        return

    logger.info("[prefetch] %s 종목 %d개 사전 수집 시작", market, len(stocks))

    # OHLCV + 투자자 데이터 (병렬 처리 없이 순차 — Railway free tier 고려)
    stocks_news: dict[str, list] = {}
    for stock in stocks:
        ticker = stock["ticker"]
        name = stock.get("name", ticker)
        try:
            market_data.fetch_ohlcv(ticker, market)
            investor_flow.get_flow(ticker, market)
            news = news_scraper.get_news(ticker, market, name)
            if news:
                stocks_news[name] = news
        except Exception as e:
            logger.warning("[prefetch] %s %s 실패: %s", market, ticker, e)

    # 뉴스 배치 감성 분석 (5개씩 묶어서)
    if stocks_news:
        try:
            sentiment.analyze_batch(stocks_news)
        except Exception as e:
            logger.warning("[prefetch] 감성 분석 실패: %s", e)

    logger.info("[prefetch] %s 완료", market)


def _keepalive() -> None:
    """Railway 컨테이너 슬립 방지 — 10분마다 자체 핑."""
    try:
        port = int(os.environ.get("PORT", 5000))
        urllib.request.urlopen(f"http://localhost:{port}/api/health", timeout=5)
    except Exception:
        pass


def start_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone="Asia/Seoul")

    # KRX 장 시작 전: 평일 08:55 KST
    _scheduler.add_job(
        lambda: _prefetch_market("KRX"),
        CronTrigger(day_of_week="mon-fri", hour=8, minute=55, timezone="Asia/Seoul"),
        id="prefetch_krx",
        replace_existing=True,
    )

    # US 장 시작 전: 평일 21:25 KST (NYSE 22:30 개장)
    _scheduler.add_job(
        lambda: _prefetch_market("US"),
        CronTrigger(day_of_week="mon-fri", hour=21, minute=25, timezone="Asia/Seoul"),
        id="prefetch_us",
        replace_existing=True,
    )

    # Railway 슬립 방지: 10분마다 자체 핑
    _scheduler.add_job(
        _keepalive,
        "interval",
        minutes=10,
        id="keepalive",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("prefetch 스케줄러 시작 (KRX 08:55, US 21:25 KST, keepalive 10분)")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
