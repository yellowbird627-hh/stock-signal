import logging
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from . import cache as _cache

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def get_news(ticker: str, market: str, company_name: str = "") -> list[dict]:
    cache_key = f"{market}:{ticker}:news_headlines"
    cached = _cache.get(cache_key, "news_headlines")
    if cached is not None:
        return cached

    if market == "KRX":
        items = _naver_news(ticker.zfill(6))
    else:
        items = _yahoo_rss(ticker)

    _cache.set(cache_key, "news_headlines", items)
    return items


def _naver_news(ticker: str, max_items: int = 5) -> list[dict]:
    url = f"https://finance.naver.com/item/news_news.naver?code={ticker}&page=1&sm=title_entity_id.basic&clusterId="
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = []
        cutoff = datetime.now() - timedelta(days=7)

        for row in soup.select("table.type5 tr"):
            title_tag = row.select_one("td.title a")
            date_tag = row.select_one("td.date")
            if not title_tag or not date_tag:
                continue

            date_str = date_tag.text.strip()
            # 네이버 날짜 형식: "2026.05.02 09:30" 또는 "05.02 09:30"
            try:
                if len(date_str) > 11:
                    pub = datetime.strptime(date_str, "%Y.%m.%d %H:%M")
                else:
                    pub = datetime.strptime(f"{datetime.now().year}.{date_str}", "%Y.%m.%d %H:%M")
                if pub < cutoff:
                    continue
                pub_str = pub.strftime("%Y-%m-%d")
            except ValueError:
                pub_str = date_str

            items.append({
                "headline": title_tag.text.strip(),
                "url": "https://finance.naver.com" + title_tag.get("href", ""),
                "snippet": "",
                "published_at": pub_str,
            })
            if len(items) >= max_items:
                break

        return items
    except Exception as e:
        logger.warning("네이버 뉴스 스크래핑 실패 (%s): %s", ticker, e)
        return []


def _yahoo_rss(ticker: str, max_items: int = 5) -> list[dict]:
    try:
        import feedparser
        url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        feed = feedparser.parse(url)
        cutoff = datetime.now() - timedelta(days=7)
        items = []

        for entry in feed.entries:
            try:
                pub = datetime(*entry.published_parsed[:6])
            except Exception:
                pub = datetime.now()

            if pub < cutoff:
                continue

            items.append({
                "headline": entry.get("title", ""),
                "url": entry.get("link", ""),
                "snippet": entry.get("summary", "")[:300],
                "published_at": pub.strftime("%Y-%m-%d"),
            })
            if len(items) >= max_items:
                break

        return items
    except Exception as e:
        logger.warning("Yahoo RSS 실패 (%s): %s", ticker, e)
        return []
