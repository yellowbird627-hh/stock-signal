export type Market = "KRX" | "US"
export type SignalLabel = "none" | "weak" | "moderate" | "strong" | "very_strong"
export type Suitability = "low" | "medium" | "high"

export interface SignalBreakdown {
  score: number
  max: number
  detail: string
}

export interface SignalScore {
  total: number
  base: number
  confluence_bonus: number
  confluence_count: number
  label: SignalLabel
  breakdown: Record<string, SignalBreakdown>
}

export interface NewsItem {
  headline: string
  url: string
  sentiment_score: number
  published_at: string
}

export interface NewsSentiment {
  score: number
  confidence: number
  key_points: string[]
  reasoning: string
}

export interface SignalResult {
  ticker: string
  market: Market
  company_name: string
  price: number
  change_pct: number
  trading_suitability: Suitability
  atr_pct: number
  data_timestamp: string
  per?: number | null
  pbr?: number | null
  price_levels?: {
    ma20: number
    ma60: number | null
    bb_mid: number
    bb_upper: number
    high_30d: number
    atr: number
  }
  buy: SignalScore
  sell: SignalScore
  news: NewsItem[]
  news_sentiment: NewsSentiment
  data_limitations: string[]
}

export interface PortfolioItem {
  ticker: string
  market: Market
  name: string
  buy: number
  sell: number
  buy_label: SignalLabel
  sell_label: SignalLabel
  confluence_bonus: number
  price: number
  change_pct: number
  suitability: Suitability
  atr_pct: number
  error?: string
}

export interface PortfolioResponse {
  generated_at: string
  count: number
  stocks: PortfolioItem[]
}

export interface RecommendationItem {
  ticker: string
  name: string
  timing: string
  reason: string
  target1?: number
  target2?: number
  stop_loss?: number
}

export interface Recommendation {
  buy: RecommendationItem[]
  sell: RecommendationItem[]
  summary: string
  generated_at?: string
}

export interface StockConfig {
  ticker: string
  market: Market
  name: string
  sector?: string
  enabled: boolean
}
