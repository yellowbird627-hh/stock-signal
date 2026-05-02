# stock-signal 코드맵 & 개발 가이드

## 배포 현황

| | URL |
|--|-----|
| 백엔드 (Railway) | `https://stock-signal-production.up.railway.app` |
| 프론트엔드 (Vercel) | `https://stock-signal-chi.vercel.app` |
| GitHub | `https://github.com/yellowbird627-hh/stock-signal` |

---

## 전체 파일 구조

```
stock-signal/
├── backend/
│   ├── app.py                    # Flask 앱 진입점 + 모든 API 엔드포인트
│   ├── config/stocks.json        # 관리 종목 목록 (ticker, market, name, enabled)
│   └── services/
│       ├── cache.py              # 인메모리 TTL 캐시
│       ├── market_data.py        # OHLCV 수집 (KRX: FinanceDataReader, US: yfinance)
│       ├── technical.py          # 기술 지표 계산 (RSI/MACD/볼린저/스토캐스틱/ATR 등)
│       ├── investor_flow.py      # 기관·외국인 순매수, 공매도 비율 (pykrx)
│       ├── news_scraper.py       # 뉴스 수집 (KRX: 네이버금융, US: Yahoo RSS)
│       ├── sentiment.py          # Gemini AI 뉴스 감성 분석 (배치 5종목씩)
│       ├── scorer.py             # 신호 점수 집계 (B1-B10, S1-S10 + 컨플루언스)
│       ├── recommendation.py     # Gemini AI 매수/매도 추천 생성
│       └── prefetch.py           # 스케줄러 (KRX 08:55, US 21:25 KST 사전 수집)
└── frontend/
    ├── app/
    │   ├── layout.tsx            # 루트 레이아웃
    │   └── page.tsx              # 메인 페이지 (탭 4개 관리)
    ├── components/
    │   ├── panels/
    │   │   ├── PortfolioDashboard.tsx  # 전체 포트폴리오 테이블 + 종목 추가/삭제
    │   │   ├── AIRecommendation.tsx    # AI 매수/매도 추천 패널
    │   │   ├── BuyScoreCard.tsx        # 매수 신호 상세 (B1-B10 진행바)
    │   │   ├── SellScoreCard.tsx       # 매도 신호 상세 (S1-S10 진행바)
    │   │   ├── NewsSentimentPanel.tsx  # 뉴스 목록 + 감성 분석 결과
    │   │   ├── StockSearch.tsx         # 개별 종목 검색 입력
    │   │   └── IndicatorGuide.tsx      # 20개 지표 설명 가이드 (정적)
    │   └── ui/
    │       ├── ScoreGauge.tsx          # 점수 게이지 바 (buy/sell 색상 분기)
    │       └── TradingSuitability.tsx  # 단타 적합도 배지 (high/medium/low)
    ├── lib/api.ts                # 백엔드 API 호출 함수 모음
    ├── store/useSignalStore.ts   # Zustand 전역 상태 (포트폴리오, 종목, 탭)
    └── types/index.ts            # TypeScript 타입 정의 전체
```

---

## 데이터 흐름

```
사용자 요청
    ↓
app.py → _analyze_stock(ticker, market)
    ├── market_data.fetch_ohlcv()       → OHLCV DataFrame (캐시 15분)
    ├── technical.compute_all()         → 8개 기술 지표 dict
    ├── investor_flow.get_flow()        → 기관·외국인·공매도 데이터 (캐시 30분)
    │       └── 장외/주말 실패 시 → data/flow_cache/*.json 파일에서 복원
    ├── news_scraper.get_news()         → 뉴스 헤드라인 최대 5개 (캐시 60분)
    ├── sentiment.analyze_batch()       → Gemini AI 감성 점수 0.0~1.0 (캐시 120분)
    └── scorer.compute_scores()         → buy/sell 점수 0~100 + 라벨
```

---

## API 엔드포인트 (app.py)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/health` | 서버 상태 확인 |
| GET | `/api/stocks` | 전체 종목 목록 반환 |
| POST | `/api/stocks` | 종목 추가 (body: `{ticker, market}`) |
| DELETE | `/api/stocks/<market>/<ticker>` | 종목 삭제 |
| GET | `/api/signal?ticker=&market=` | 단일 종목 전체 분석 |
| GET | `/api/portfolio` | 활성 종목 전체 점수 요약 |
| GET | `/api/recommendation` | Gemini AI 매수/매도 추천 |
| POST | `/api/refresh-cache` | 특정 종목 캐시 무효화 (body: `{ticker, market}`) |

---

## 점수 시스템 (scorer.py)

각 신호는 `{"score": int, "max": int, "detail": str}` 구조.  
`_sig(score, max, detail)` 헬퍼로 생성.

**매수 신호 (B1-B10)**

| 코드 | 지표 | 최대 (KRX/US) |
|------|------|--------------|
| B1 | 기관+외국인 동반 순매수 | 25 / 0 (US 재분배) |
| B2 | 30일 고점 대비 하락 | 15 |
| B3 | 뉴스 긍정 감성 | 15 |
| B4 | RSI 과매도 | 10 / 20 |
| B5 | MACD 골든크로스 | 8 |
| B6 | 거래량 급증+양봉 | 5 |
| B7 | 볼린저 하단 | 8 / 15 |
| B8 | 스토캐스틱 과매도 | 7 / 15 |
| B9 | 공매도 감소 / Put-Call 하락 | 4 |
| B10 | 이평선 정배열 | 3 |

**매도 신호 (S1-S10)**: B1-B10의 반대 조건, 동일 점수 구조.

**컨플루언스 보너스**: 6개 카테고리 중 4개 이상 동시 충족 시 +10점.

**점수 → 라벨**

| 범위 | 라벨 |
|------|------|
| 0~30 | none |
| 31~50 | weak |
| 51~70 | moderate |
| 71~85 | strong |
| 86~100 | very_strong |

---

## 핵심 타입 (types/index.ts)

```typescript
SignalBreakdown  { score, max, detail }
SignalScore      { total, base, confluence_bonus, confluence_count, label, breakdown }
SignalResult     { ticker, market, company_name, price, change_pct, buy, sell, news, news_sentiment, data_limitations }
PortfolioItem    { ticker, market, name, buy, sell, buy_label, sell_label, price, change_pct, suitability, atr_pct }
Recommendation   { buy: RecommendationItem[], sell: RecommendationItem[], summary }
```

---

## 캐시 레이어 (cache.py)

인메모리 dict. 프로세스 재시작 시 초기화.

| 레이어 | TTL |
|--------|-----|
| ohlcv | 15분 |
| investor_flow | 30분 |
| short_ratio | 30분 |
| news_headlines | 60분 |
| news_sentiment | 120분 |

KRX 기관·공매도 데이터는 추가로 `data/flow_cache/KRX_{ticker}_{kind}.json`에 파일 저장 → 주말·장외에도 마지막 거래일 데이터 제공.

---

## AI 연동 (Gemini)

- 패키지: `google-genai` (`from google import genai`)
- 모델: `gemini-2.5-flash`
- `sentiment.py`: 종목별 뉴스 헤드라인 → 감성 점수 (0.0~1.0)
- `recommendation.py`: 포트폴리오 신호 데이터 → 매수/매도 추천 JSON

---

## 주요 규칙

- `load_dotenv()`는 서비스 모듈 import **전**에 호출 (app.py 최상단)
- `ACCESS_PASSWORD` 환경변수 설정 금지 — 설정 시 모든 API 요청 차단
- Railway `PORT`는 자동 주입 → 수동 설정 불필요
- Vercel **Root Directory** = `frontend`, **Deployment Protection** = 비활성화

---

## 로컬 실행

```bash
# 백엔드 (포트 5100)
cd backend && python app.py

# 프론트엔드 (포트 3001)
cd frontend && npm run dev -- -p 3001
```

포트 충돌 시: `lsof -ti :5100 | xargs kill -9`

## 배포

```bash
git add <파일> && git commit -m "설명" && git push origin main
# Railway·Vercel 자동 재배포
```
