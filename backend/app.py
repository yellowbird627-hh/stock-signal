import json
import logging
import os
import time as _time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()  # 서비스 import 전에 .env 로드

from flask import Flask, jsonify, request
from flask_cors import CORS

from services import cache as _cache
from services import backtest as backtest_svc, investor_flow, market_data, news_scraper, recommendation as recommendation_svc, scorer, sentiment, technical
from services.prefetch import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=os.environ.get("FRONTEND_ORIGIN", "*"))

_DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "stocks.json")
_VOLUME_CONFIG_PATH = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", ""), "stocks.json")

def _get_config_path() -> str:
    mount = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "")
    if mount and os.path.isdir(mount):
        path = os.path.join(mount, "stocks.json")
        if not os.path.exists(path):
            with open(_DEFAULT_CONFIG_PATH, encoding="utf-8") as f:
                default_data = json.load(f)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            logger.info("Volume에 stocks.json 초기화 완료: %s", path)
        return path
    return _DEFAULT_CONFIG_PATH

CONFIG_PATH = _get_config_path()

# KRX 전체 종목 목록 캐시 (24시간 유지)
_krx_listing: dict = {"data": None, "loaded_at": 0.0}


def _load_krx_listing() -> list[dict]:
    now = _time.time()
    if _krx_listing["data"] is not None and now - _krx_listing["loaded_at"] < 86400:
        return _krx_listing["data"]
    import FinanceDataReader as fdr
    df = fdr.StockListing("KRX")
    result = []
    for _, row in df.iterrows():
        code = str(row.get("Code", row.get("Symbol", ""))).zfill(6)
        name = str(row.get("Name", ""))
        if code and name and name != "nan":
            result.append({"ticker": code, "name": name, "market": "KRX"})
    _krx_listing["data"] = result
    _krx_listing["loaded_at"] = now
    logger.info("KRX 종목 목록 캐시 갱신: %d 종목", len(result))
    return result


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _load_stocks() -> list[dict]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("stocks", [])


def _analyze_stock(ticker: str, market: str) -> dict:
    """단일 종목 전체 분석 파이프라인."""
    # 1. OHLCV
    df = market_data.fetch_ohlcv(ticker, market)
    price = float(df["Close"].iloc[-1])
    prev_price = float(df["Close"].iloc[-2]) if len(df) >= 2 else price
    change_pct = round((price - prev_price) / prev_price * 100, 2) if prev_price else 0

    # 2. 기술 지표
    tech = technical.compute_all(df)

    # 3. 기관/외국인 흐름
    flow = investor_flow.get_flow(ticker, market)

    # 4. 뉴스 수집
    stock_name = _get_stock_name(ticker, market)
    news_items = news_scraper.get_news(ticker, market, stock_name)

    # 5. 감성 분석 (배치 — 1종목이어도 배치 함수 사용)
    sentiment_results = sentiment.analyze_batch({stock_name: news_items})
    sent = sentiment_results.get(stock_name, {"sentiment_score": 0.5, "confidence": 0.0,
                                              "key_points": [], "reasoning": "뉴스 없음"})
    sentiment_score = float(sent.get("sentiment_score", 0.5))

    # 6. 점수 계산
    scores = scorer.compute_scores(flow, tech, sentiment_score, market)

    # 7. PER/PBR
    fundamentals = market_data.get_fundamentals(ticker, market)

    # 8. 데이터 제한 안내
    limitations = []
    if flow.get("data_error"):
        limitations.append(f"기관/외국인 데이터: {flow['data_error']}")
    if market == "US":
        limitations.append("미국 주식: 일별 기관/외국인 데이터 없음 — B1/S1 점수가 타 지표로 재분배됨")

    return {
        "ticker": ticker,
        "market": market,
        "company_name": stock_name,
        "price": price,
        "change_pct": change_pct,
        "trading_suitability": tech["atr"]["suitability"],
        "atr_pct": tech["atr"]["atr_pct"],
        "data_timestamp": datetime.now(timezone.utc).isoformat(),
        "per": fundamentals.get("per"),
        "pbr": fundamentals.get("pbr"),
        "price_levels": {
            "ma20":     tech["ma_alignment"]["ma20"],
            "ma60":     tech["ma_alignment"]["ma60"],
            "bb_mid":   tech["bollinger"]["mid"],
            "bb_upper": tech["bollinger"]["upper"],
            "high_30d": tech["price_position"]["high_30d"],
            "atr":      round(tech["atr"]["atr"], 2),
        },
        "buy": scores["buy"],
        "sell": scores["sell"],
        "news": [
            {
                "headline": n["headline"],
                "url": n["url"],
                "sentiment_score": sentiment_score,
                "published_at": n["published_at"],
            }
            for n in news_items
        ],
        "news_sentiment": {
            "score": sentiment_score,
            "confidence": sent.get("confidence", 0),
            "key_points": sent.get("key_points", []),
            "reasoning": sent.get("reasoning", ""),
        },
        "data_limitations": limitations,
    }


def _get_stock_name(ticker: str, market: str) -> str:
    stocks = _load_stocks()
    for s in stocks:
        if s["ticker"] == ticker and s["market"] == market:
            return s.get("name", ticker)
    return ticker


# ── API 엔드포인트 ────────────────────────────────────────────────────────────

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})


@app.route("/api/stocks")
def stocks():
    return jsonify(_load_stocks())


@app.route("/api/stocks/search")
def search_stocks():
    q = request.args.get("q", "").strip()
    market = request.args.get("market", "KRX").strip().upper()

    if not q or market not in ("KRX", "US"):
        return jsonify([])

    try:
        if market == "KRX":
            listing = _load_krx_listing()
            q_lower = q.lower()
            matches = [s for s in listing if q_lower in s["name"].lower()]
            return jsonify(matches[:10])
    except Exception as e:
        logger.error("search_stocks 오류: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500

    return jsonify([])


@app.route("/api/signal")
def signal():
    ticker = request.args.get("ticker", "").strip().upper()
    market = request.args.get("market", "KRX").strip().upper()

    if not ticker:
        return jsonify({"error": "ticker 파라미터 필요"}), 400
    if market not in ("KRX", "US"):
        return jsonify({"error": "market은 KRX 또는 US"}), 400

    try:
        result = _analyze_stock(ticker, market)
        return jsonify(result)
    except Exception as e:
        logger.error("signal 오류 (%s %s): %s", market, ticker, e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/portfolio")
def portfolio():
    stocks = [s for s in _load_stocks() if s.get("enabled", True)]

    def _analyze_one(stock):
        ticker = stock["ticker"]
        mkt = stock["market"]
        try:
            data = _analyze_stock(ticker, mkt)
            return {
                "ticker": ticker,
                "market": mkt,
                "name": stock.get("name", ticker),
                "buy": data["buy"]["total"],
                "sell": data["sell"]["total"],
                "buy_label": data["buy"]["label"],
                "sell_label": data["sell"]["label"],
                "confluence_bonus": data["buy"]["confluence_bonus"],
                "price": data["price"],
                "change_pct": data["change_pct"],
                "suitability": data["trading_suitability"],
                "atr_pct": data["atr_pct"],
            }
        except Exception as e:
            logger.warning("portfolio 분석 실패 (%s): %s", ticker, e)
            return {
                "ticker": ticker, "market": mkt,
                "name": stock.get("name", ticker),
                "buy": 0, "sell": 0, "price": 0, "change_pct": 0,
                "suitability": "low", "atr_pct": 0,
                "error": str(e),
            }

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(_analyze_one, stocks))

    results.sort(key=lambda x: x["buy"] - x["sell"], reverse=True)

    return jsonify({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "stocks": results,
    })


@app.route("/api/stocks", methods=["POST"])
def add_stock():
    body = request.get_json(silent=True) or {}
    ticker = body.get("ticker", "").strip().upper()
    market = body.get("market", "").strip().upper()

    if not ticker or market not in ("KRX", "US"):
        return jsonify({"error": "ticker와 market(KRX|US) 필요"}), 400

    if market == "KRX":
        ticker = ticker.zfill(6)

    # stocks.json 읽기
    with open(CONFIG_PATH, encoding="utf-8") as f:
        data = json.load(f)

    # 중복 확인
    for s in data["stocks"]:
        if s["ticker"] == ticker and s["market"] == market:
            return jsonify({"error": "이미 등록된 종목입니다"}), 409

    # 회사명 자동 조회
    name = body.get("name", "").strip()
    if not name:
        try:
            name = market_data.get_company_name(ticker, market)
        except Exception:
            name = ticker

    data["stocks"].append({
        "ticker": ticker,
        "market": market,
        "name": name,
        "enabled": True,
    })

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("종목 추가: %s %s (%s)", market, ticker, name)
    return jsonify({"ok": True, "ticker": ticker, "market": market, "name": name})


@app.route("/api/stocks/<market>/<ticker>", methods=["DELETE"])
def remove_stock(market: str, ticker: str):
    market = market.upper()
    ticker = ticker.upper()
    if market == "KRX":
        ticker = ticker.zfill(6)

    with open(CONFIG_PATH, encoding="utf-8") as f:
        data = json.load(f)

    before = len(data["stocks"])
    data["stocks"] = [
        s for s in data["stocks"]
        if not (s["ticker"] == ticker and s["market"] == market)
    ]

    if len(data["stocks"]) == before:
        return jsonify({"error": "종목을 찾을 수 없습니다"}), 404

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    _cache.invalidate_ticker(ticker, market)
    logger.info("종목 삭제: %s %s", market, ticker)
    return jsonify({"ok": True})


@app.route("/api/recommendation")
def get_recommendation():
    stocks_cfg = [s for s in _load_stocks() if s.get("enabled", True)]

    def _build_rec_item(stock):
        ticker = stock["ticker"]
        mkt = stock["market"]
        try:
            data = _analyze_stock(ticker, mkt)
            buy_active = {k: v for k, v in data["buy"]["breakdown"].items() if v["score"] > 0}
            sell_active = {k: v for k, v in data["sell"]["breakdown"].items() if v["score"] > 0}
            limitations = data.get("data_limitations", [])
            return {
                "ticker": ticker,
                "market": mkt,
                "name": stock.get("name", ticker),
                "buy": data["buy"]["total"],
                "sell": data["sell"]["total"],
                "buy_label": data["buy"]["label"],
                "sell_label": data["sell"]["label"],
                "buy_active": buy_active,
                "sell_active": sell_active,
                "data_limitation": limitations[0] if limitations else "",
                "price": data["price"],
                "price_levels": data.get("price_levels", {}),
            }
        except Exception as e:
            logger.warning("recommendation 분석 실패 (%s): %s", ticker, e)
            return None

    with ThreadPoolExecutor(max_workers=5) as executor:
        portfolio_data = [r for r in executor.map(_build_rec_item, stocks_cfg) if r is not None]

    result = recommendation_svc.get_recommendation(portfolio_data)
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    return jsonify(result)


@app.route("/api/backtest")
def run_backtest():
    ticker    = request.args.get("ticker", "").strip().upper()
    market    = request.args.get("market", "KRX").strip().upper()
    threshold = int(request.args.get("threshold", 25))
    hold_days = int(request.args.get("hold_days", 5))

    if not ticker:
        return jsonify({"error": "ticker 파라미터 필요"}), 400
    if market not in ("KRX", "US"):
        return jsonify({"error": "market은 KRX 또는 US"}), 400
    threshold = max(20, min(90, threshold))
    hold_days = max(1, min(20, hold_days))

    try:
        result = backtest_svc.run_backtest(ticker, market, threshold, hold_days)
        return jsonify(result)
    except Exception as e:
        logger.error("backtest 오류 (%s %s): %s", market, ticker, e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/refresh-cache", methods=["POST"])
def refresh_cache():
    body = request.get_json(silent=True) or {}
    ticker = body.get("ticker", "").upper()
    market = body.get("market", "").upper()

    if ticker and market:
        _cache.invalidate_ticker(ticker, market)
        return jsonify({"ok": True, "invalidated": f"{market}:{ticker}"})
    return jsonify({"error": "ticker와 market 필요"}), 400


# ── 앱 시작/종료 ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    start_scheduler()
    port = int(os.environ.get("PORT", 5000))
    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    finally:
        stop_scheduler()
